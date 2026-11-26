"""Compare the editor's committed reading with the AI reading (Method E.6, reconciliation).

Both inputs are CSV files with the same columns and a key column. The output lists every
core field that differs. The editor resolves each difference at the page; this script never
decides which value is right.

Run: python scripts/compare.py editor.csv ai.csv KEY_COLUMN [out.csv]
"""
import csv
import sys

CORE = ["quote_original", "metric", "direction", "promised_value", "observation_date",
        "consequence_summary", "reported_value", "statement_quote", "status", "status_basis"]


def norm(value: str) -> str:
    return " ".join((value or "").split()).lower()


def compare(editor: list, ai: list, key: str) -> list:
    ed = {r[key]: r for r in editor}
    ai_rows = {r[key]: r for r in ai}
    diffs = []
    for k in sorted(set(ed) | set(ai_rows)):
        if k not in ed:
            diffs.append((k, "(row)", "", "only in the AI reading"))
            continue
        if k not in ai_rows:
            diffs.append((k, "(row)", "only in the editor's reading", ""))
            continue
        for field in CORE:
            if field in ed[k] and norm(ed[k].get(field)) != norm(ai_rows[k].get(field)):
                diffs.append((k, field, ed[k].get(field, ""), ai_rows[k].get(field, "")))
    return diffs


def main() -> None:
    if len(sys.argv) < 4:
        sys.exit("usage: python scripts/compare.py editor.csv ai.csv KEY [out.csv]")
    load = lambda p: list(csv.DictReader(open(p, newline="", encoding="utf-8")))
    diffs = compare(load(sys.argv[1]), load(sys.argv[2]), sys.argv[3])
    out = sys.argv[4] if len(sys.argv) > 4 else "differences.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        # Values are shown as A and B without saying which is the editor's, for the auditor's copy.
        w.writerow(["key", "field", "value_A", "value_B", "resolution", "reason"])
        for d in diffs:
            w.writerow(list(d) + ["", ""])
    print(f"{len(diffs)} difference(s) written to {out}")


if __name__ == "__main__":
    main()
