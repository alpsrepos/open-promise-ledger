"""Draft the issuer notice (Method Appendix C) from a record folder.

Usage: python scripts/notice.py RECORD_DIR PUBLICATION_DATE [REPLY_BY_DATE] > notice.md

The fixed text is copied from METHOD.md at run time, so the notice always carries the text
in force. The editor reads every notice before it is sent; nothing is sent by this script.
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fixed_text():
    method = (ROOT / "METHOD.md").read_text(encoding="utf-8")
    m = re.search(r'\*\*Notice\.\*\*.*?It states: "(.*?)" One reminder', method, re.S)
    if not m:
        sys.exit("fixed notice text not found in METHOD.md")
    return m.group(1)


def read(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main(record, pub, reply_by=""):
    inst = {r["instrument_id"]: r for r in read(record / "instruments.csv")}
    prom = {r["promise_id"]: r for r in read(record / "promises.csv")}
    obs = read(record / "observations.csv")
    links = read(record / "links.csv")
    name = next(iter(inst.values()))["issuer_name_terms"]
    out = [f"Subject: Open Promise Ledger: lines on {name} before publication on {pub}", "",
           "Dear Investor Relations team,", "",
           "The Open Promise Ledger (openpromise.org) is a free, non-commercial research record of the targets "
           "in sustainability-linked bonds and of what issuers later reported. The lines below concern your bonds. "
           f"They are planned for publication on {pub}.", "", fixed_text(), ""]
    if reply_by:
        out += [f"Replies received by {reply_by} are published with the lines.", ""]
    for n, l in enumerate(links, start=1):
        i, p = inst[l["instrument_id"]], prom[l["promise_id"]]
        translated = "read via machine translation" in (l.get("flags", "") + p.get("flags", ""))
        out += [f"Line {n}. Bond {i['isins'].replace(';', ', ')}" + (" (checked through the AI's translation)" if translated else ""),
                f"- Target as written in the terms: \"{p['quote_original']}\" ({p['quote_source_id']}, page {p['quote_page']})",
                f"- Observation date: {p['observation_date']}; reporting deadline: {p['reporting_deadline'] or 'none in the terms'}"]
        for o in [o for o in obs if o["promise_id"] == p["promise_id"]]:
            out.append(f"- Reported: {o['reported_value']} {o['reported_unit']} ({o['source_id']}, page {o['page']})")
        out.append(f"- Status in the record: {l['status']} (basis: {l['status_basis']})")
        if l.get("statement_quote"):
            out.append(f"- Statement relied on: \"{l['statement_quote']}\" ({l['statement_source_id']})")
        out.append(f"- Consequence in the record: {l['consequence_taking_effect']}")
        out.append("")
    out += ["Kind regards,", "Ismet Alp Ceylan", "Editor, Open Promise Ledger", "openpromise.org"]
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    print(main(Path(sys.argv[1]), sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""))
