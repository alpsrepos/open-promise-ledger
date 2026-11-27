"""Compare two AI readings, or a reading with the final record, without relying on row ids.

Usage: python scripts/readings.py DIR_A DIR_B [out.csv]

Rows are matched by content, because two readings name their rows differently:
  instruments by ISIN; promises by the words of the target quote in any order (layouts differ) and the observation date;
  observations by promise, period end, source and reported value; links by instrument and promise.
Every core field that differs, and every row found in only one reading, is listed. The editor
resolves each difference at the page; the script never decides which value is right.
"""
import csv
import re
import sys
from pathlib import Path

CORE = {
    "instruments": ["isins", "issuer_name_terms", "issue_date", "maturity_date", "first_call_date",
                    "amount_million", "currency", "state"],
    "promises": ["metric", "unit", "direction", "target_form", "baseline_value", "baseline_period",
                 "promised_value", "observation_date", "reporting_deadline", "quote_source_id", "quote_page"],
    "links": ["consequence_quote", "status", "status_basis", "consequence_taking_effect"],
    "observations": ["reported_value", "reported_unit", "source_id", "page", "external_reviewer"],
}


def norm(v):
    v = (v or "").lower().replace("–", "-").replace("’", "'")
    return re.sub(r"\s+", " ", v).strip(" .")


def read(d, t):
    p = Path(d) / f"{t}.csv"
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(v):
    m = re.search(r"-?\d[\d,]*\.?\d*", v or "")
    return m.group().replace(",", "") if m else norm(v)


def keys(d):
    inst = {r["instrument_id"]: r["isins"].split(";")[0].strip() for r in read(d, "instruments")}
    prom = {}
    for r in read(d, "promises"):
        words = sorted(set(re.findall(r"[a-z0-9]+", norm(r.get("quote_original", "")))))
        prom[r["promise_id"]] = " ".join(words)[:80] + "|" + r.get("observation_date", "")
    k = {
        "instruments": {inst[r["instrument_id"]]: r for r in read(d, "instruments")},
        "promises": {prom[r["promise_id"]]: r for r in read(d, "promises")},
        "links": {inst.get(r["instrument_id"], r["instrument_id"]) + "|" + prom.get(r["promise_id"], r["promise_id"]): r
                  for r in read(d, "links")},
        "observations": {},
    }
    for r in read(d, "observations"):
        kk = "|".join([prom.get(r["promise_id"], r["promise_id"]), r.get("period_end", ""), num(r.get("reported_value"))])
        k["observations"][kk] = r
    return k


def source_map(d):
    """source id -> first 12 characters of the file hash, so readings that number sources differently compare."""
    return {r["source_id"]: (r.get("sha256") or r["source_id"])[:12] for r in read(d, "sources")}


def compare(a, b):
    ka, kb = keys(a), keys(b)
    sa, sb = source_map(a), source_map(b)
    out = []
    for t, fields in CORE.items():
        for key in sorted(set(ka[t]) | set(kb[t])):
            ra, rb = ka[t].get(key), kb[t].get(key)
            if ra is None or rb is None:
                out.append((t, key, "(row)", "" if ra is None else "present", "" if rb is None else "present"))
                continue
            for f in fields:
                va, vb = ra.get(f, ""), rb.get(f, "")
                if f in {"source_id", "quote_source_id"}:
                    va, vb = sa.get(va, va), sb.get(vb, vb)
                if f in {"reported_value", "promised_value", "baseline_value", "amount_million"}:
                    same = num(va) == num(vb)
                else:
                    same = norm(va) == norm(vb)
                if not same:
                    out.append((t, key, f, va, vb))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    diffs = compare(sys.argv[1], sys.argv[2])
    rows = [dict(zip(["table", "match_key", "field", "value_A", "value_B"], d)) for d in diffs]
    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["table", "match_key", "field", "value_A", "value_B"])
            w.writeheader()
            w.writerows(rows)
    by = {}
    for r in rows:
        by.setdefault((r["table"], r["field"] == "(row)"), 0)
        by[(r["table"], r["field"] == "(row)")] += 1
    for (t, isrow), n in sorted(by.items()):
        print(f"{t}: {n} {'rows in one reading only' if isrow else 'field differences'}")
    print(f"{len(rows)} difference(s)")
