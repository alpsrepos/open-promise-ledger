"""Build the AI auditor's sheet from a record folder (Method E.7, "AI audit").

Usage: python scripts/audit_sheet.py RECORD_DIR OUT.csv [SEED]

One line per value the audit must check, including the cited source and page themselves (is the quote on that page?): for every link, the core fields, unit, perimeter,
reporting deadline, and status with basis; the other fields on ten random links (drawn with
SEED, default 1). Each line carries the value, source id, page and quote where the record
holds them, so the auditor opens the page directly.
"""
import csv
import random
import sys
from pathlib import Path

CORE_PROMISE = ["quote_source_id", "quote_page", "quote_original", "metric", "unit", "direction", "perimeter", "promised_value",
                "baseline_value", "baseline_period", "observation_date", "reporting_deadline"]
CORE_LINK = ["consequence_quote", "status", "status_basis", "status_date", "statement_quote",
             "consequence_taking_effect"]
CORE_OBS = ["source_id", "page", "reported_value", "reported_unit", "reported_perimeter", "value_quote",
            "external_reviewer", "deadline_relation"]
OTHER_INST = ["isins", "issue_date", "maturity_date", "first_call_date", "amount_million", "currency",
              "state", "state_date", "caps_and_joint_triggers"]


def read(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main(record, out, seed=1):
    inst = {r["instrument_id"]: r for r in read(record / "instruments.csv")}
    prom = {r["promise_id"]: r for r in read(record / "promises.csv")}
    links = read(record / "links.csv")
    obs = read(record / "observations.csv")
    lines = []

    def add(lid, table, row_id, field, value, src="", page="", quote=""):
        lines.append({"line_id": f"A-{len(lines) + 1:04d}", "link_id": lid, "table": table, "row_id": row_id,
                      "field": field, "record_value": value, "source_id": src, "page": page, "quote": quote,
                      "agree": "", "page_says": "", "note": ""})

    seen_p, seen_o = set(), set()
    for l in links:
        p = prom[l["promise_id"]]
        if p["promise_id"] not in seen_p:
            seen_p.add(p["promise_id"])
            for f in CORE_PROMISE:
                add(l["link_id"], "promises", p["promise_id"], f, p.get(f, ""), p.get("quote_source_id", ""),
                    p.get("quote_page", ""), p.get("quote_original", ""))
            for o in obs:
                if o["promise_id"] == p["promise_id"] and o["observation_id"] not in seen_o:
                    seen_o.add(o["observation_id"])
                    for f in CORE_OBS:
                        add(l["link_id"], "observations", o["observation_id"], f, o.get(f, ""),
                            o.get("source_id", ""), o.get("page", ""), o.get("value_quote", ""))
        for f in CORE_LINK:
            src = l.get("statement_source_id", "") if f in {"status", "status_basis", "statement_quote"} else ""
            add(l["link_id"], "links", l["link_id"], f, l.get(f, ""), src, "",
                l.get("statement_quote", "") if src else "see the terms and the instrument's notes")
    rnd = random.Random(seed)
    sample = rnd.sample(links, min(10, len(links)))
    for l in sample:
        i = inst[l["instrument_id"]]
        for f in OTHER_INST:
            add(l["link_id"], "instruments", i["instrument_id"], f, i.get(f, ""), i.get("state_source_ids", ""))
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(lines[0].keys()))
        w.writeheader()
        w.writerows(lines)
    print(f"{len(lines)} lines for {len(links)} links; other fields on {len(sample)} random links (seed {seed})")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 1)
