"""Build the frame (Method section 2, E.2, E.3) from the registered inputs.

Inputs (registered with the frame; the Euronext file itself is kept private until its reuse terms are recorded):
  1. the Euronext ESG bonds list as downloaded (CSV), path given as argument 1
  2. the GLEIF ISIN-LEI mapping file of the same day (CSV), path given as argument 2
  3. frame/isin-overrides.json: LEIs set for single ISINs after the check
  4. frame/name-match-picks.json: LEIs chosen by name match for issuers the mapping file does not cover
     (each to be checked by the editor; see frame/lei-name-matches-to-check.csv)

Steps:
  - keep rows whose Bond Type is "Sustainability-Linked Bond" (case ignored); one row per ISIN,
    first listing date kept;
  - LEI of the issuer: from the mapping file; else the LEI of another ISIN with the same issuer label;
    else the name-match pick; else none;
  - issuer group: the GLEIF ultimate parent of that LEI (live GLEIF API), or the entity itself where
    no parent is reported, or the issuer label where no LEI was found.

Run: python scripts/build_frame.py EURONEXT.csv ISIN_LEI.csv
"""
import csv
import datetime
import json
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.gleif.org/api/v1/lei-records/"


def get(url):
    try:
        return json.load(urllib.request.urlopen(url, timeout=30))
    except urllib.error.HTTPError as e:
        return {"err": e.code}


def main():
    euronext, mapping = sys.argv[1], sys.argv[2]
    raw = Path(euronext).read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    rows = [r for r in csv.DictReader(text.splitlines())
            if r["Bond Type"].strip().lower() == "sustainability-linked bond"]
    bonds = {}
    for r in rows:
        isin = r["ISIN"].strip()
        d = datetime.datetime.strptime(r["Listing Date"], "%m/%d/%Y").date()
        b = bonds.setdefault(isin, {"isin": isin, "issuer_label": r["Issuer"].strip(), "first_listing": d,
                                    "venues": set(), "amount_m": r["Amount (million)"], "currency": r["Currency"]})
        b["first_listing"] = min(b["first_listing"], d)
        b["venues"].add(r["Listing Venue"].strip().capitalize())
    isin_lei = {}
    with open(mapping, newline="") as fh:
        rd = csv.reader(fh)
        next(rd)
        for lei, isin in rd:
            if isin in bonds:
                isin_lei[isin] = lei
    by_label = defaultdict(set)
    for isin, lei in isin_lei.items():
        by_label[bonds[isin]["issuer_label"]].add(lei)
    picks = json.loads((ROOT / "frame" / "name-match-picks.json").read_text(encoding="utf-8"))
    overrides = json.loads((ROOT / "frame" / "isin-overrides.json").read_text(encoding="utf-8"))
    cache = {}

    def entity(lei):
        if lei not in cache:
            rec = get(API + lei)["data"]["attributes"]["entity"]
            par = get(API + lei + "/ultimate-parent")
            parent = None
            if par.get("data"):
                pa = par["data"]["attributes"]["entity"]
                parent = (par["data"]["id"], pa["legalName"]["name"], pa["legalAddress"]["country"])
            cache[lei] = (rec["legalName"]["name"], rec["legalAddress"]["country"], parent)
            time.sleep(0.2)
        return cache[lei]

    out = []
    for isin, b in sorted(bonds.items()):
        if isin in overrides:
            lei, src = overrides[isin], "editor check: ISIN-level correction"
        elif isin in isin_lei:
            lei, src = isin_lei[isin], "GLEIF ISIN-LEI map"
        elif by_label.get(b["issuer_label"]):
            lei, src = sorted(by_label[b["issuer_label"]])[0], "same issuer label as a mapped ISIN"
        elif picks.get(b["issuer_label"]):
            lei, src = picks[b["issuer_label"]], "name match (editor to check)"
        else:
            lei, src = None, "no LEI found"
        name = country = ""
        if lei:
            name, country, parent = entity(lei)
            gkey, gname, gcountry, gsrc = (parent + ("GLEIF ultimate parent",)) if parent else \
                (lei, name, country, "entity itself (no parent reported)")
        else:
            gkey, gname, gcountry, gsrc = "NOLEI:" + b["issuer_label"], b["issuer_label"], "", "no LEI found"
        out.append({"isin": isin, "issuer_label": b["issuer_label"], "first_listing": b["first_listing"].isoformat(),
                    "listed_by_2023": b["first_listing"] <= datetime.date(2023, 12, 31),
                    "venues": ";".join(sorted(b["venues"])), "amount_m": b["amount_m"], "currency": b["currency"],
                    "issuer_lei": lei or "", "issuer_legal_name": name, "issuer_country": country, "lei_source": src,
                    "group_lei": gkey if lei else "", "group_name": gname, "group_country": gcountry,
                    "group_source": gsrc, "group_key": gkey})
    out.sort(key=lambda x: (x["group_key"], x["isin"]))
    with open(ROOT / "frame" / "frame-bonds.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(len(out), "bonds,", len({o["group_key"] for o in out}), "groups")
    write_groups()


if __name__ == "__main__":
    main()


def write_groups():
    """Write frame/frame-groups.csv from frame/frame-bonds.csv."""
    rows = list(csv.DictReader(open(ROOT / "frame" / "frame-bonds.csv", encoding="utf-8")))
    groups = {}
    for r in rows:
        g = groups.setdefault(r["group_key"], {"group_key": r["group_key"], "group_name": r["group_name"],
                                               "group_country": r["group_country"], "group_source": r["group_source"],
                                               "bonds": 0, "bonds_listed_by_2023": 0, "issuer_labels": set()})
        g["bonds"] += 1
        g["bonds_listed_by_2023"] += r["listed_by_2023"] == "True"
        g["issuer_labels"].add(r["issuer_label"])
    with open(ROOT / "frame" / "frame-groups.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["group_key", "group_name", "group_country", "group_source", "bonds",
                                           "bonds_listed_by_2023", "issuer_labels"])
        w.writeheader()
        for k in sorted(groups):
            g = groups[k]
            g["issuer_labels"] = ";".join(sorted(g["issuer_labels"]))
            w.writerow(g)
    print(len(groups), "groups written")


if __name__ == "__main__" and len(sys.argv) == 1:
    write_groups()
