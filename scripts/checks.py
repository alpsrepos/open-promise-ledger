"""Record checks for the Open Promise Ledger.

Run: python scripts/checks.py            (checks data/ against dictionary/schema.json)
     python scripts/checks.py --words    (also scans the project's own text for wording-rule words)

Exit code 0 means every check passed.
"""
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "dictionary" / "schema.json").read_text(encoding="utf-8"))

# Wording rule (Method, Appendix C). Stems catch derived forms.
WORD_STEMS = ["verif", "certif", "assur", "safe", "risk", "avoid", "recommend", "fail", "broke", "greenwash"]
# Words that contain a stem but are allowed: quoted reviewer terms are handled by skipping quotes.
WORD_EXEMPT_LINE = "never uses: verified, certified, assured, safe, risk, avoid, recommended, failed, broke, greenwashing"
PROJECT_TEXT = ["METHOD.md", "README.md", "docs"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def isin_ok(isin: str) -> bool:
    """ISO 6166 check digit (Luhn on the letters converted to numbers)."""
    if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", isin):
        return False
    digits = "".join(str(int(c, 36)) for c in isin[:-1])
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return (10 - total % 10) % 10 == int(isin[-1])


def lei_ok(lei: str) -> bool:
    """ISO 17442 check digits (ISO 7064 MOD 97-10)."""
    if not re.fullmatch(r"[A-Z0-9]{18}[0-9]{2}", lei):
        return False
    return int("".join(str(int(c, 36)) for c in lei)) % 97 == 1


def date_ok(value: str) -> bool:
    if not DATE_RE.match(value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def check_table(name: str, rows: list) -> list:
    spec = SCHEMA["tables"][name]["fields"]
    errors = []
    for n, row in enumerate(rows, start=2):
        extra = set(row) - set(spec)
        if extra:
            errors.append(f"{name} line {n}: unknown columns {sorted(extra)}")
        for field, rule in spec.items():
            value = (row.get(field) or "").strip()
            where = f"{name} line {n}, {field}"
            if rule.get("required") and not value:
                errors.append(f"{where}: required field is empty")
                continue
            if not value:
                continue
            if "codes" in rule and value not in rule["codes"]:
                errors.append(f"{where}: '{value}' is not an allowed code")
            if "codes_multi" in rule:
                bad = [v.strip() for v in value.split(";") if v.strip() and v.strip() not in rule["codes_multi"]]
                if bad:
                    errors.append(f"{where}: not allowed {bad}")
            if field.endswith("_date") or field in {"observation_date", "period_end", "retrieved", "status_date"}:
                if not date_ok(value):
                    errors.append(f"{where}: '{value}' is not a date YYYY-MM-DD")
            if field == "isins":
                for isin in value.split(";"):
                    if not isin_ok(isin.strip()):
                        errors.append(f"{where}: ISIN check digit fails for '{isin.strip()}'")
            if field.endswith("_lei") and not lei_ok(value):
                errors.append(f"{where}: LEI check digits fail for '{value}'")
    return errors


def check_rules(tables: dict) -> list:
    """Cross-table rules from the Method that a script can recompute."""
    errors = []
    promises = {r["promise_id"]: r for r in tables.get("promises", [])}
    instruments = {r["instrument_id"]: r for r in tables.get("instruments", [])}
    for n, link in enumerate(tables.get("links", []), start=2):
        where = f"links line {n}"
        p = promises.get(link.get("promise_id"))
        i = instruments.get(link.get("instrument_id"))
        if p is None:
            errors.append(f"{where}: promise_id not in promises")
            continue
        if i is None:
            errors.append(f"{where}: instrument_id not in instruments")
            continue
        status = link.get("status", "")
        basis = link.get("status_basis", "")
        # Rule 1: an ended instrument before the observation date.
        ended = i.get("state") in {"redeemed early", "matured", "exchanged", "in default"}
        if ended and i.get("state_date") and p.get("observation_date") and i["state_date"] < p["observation_date"]:
            if status != "Ended before observation date":
                errors.append(f"{where}: instrument ended before the observation date, so rule 1 applies")
            if link.get("consequence_taking_effect") != "not applicable: instrument ended before observation date":
                errors.append(f"{where}: consequence code must be 'not applicable: instrument ended before observation date' (E.10.2)")
        # Rule 3: not yet due.
        if p.get("observation_date") and link.get("status_date") and p["observation_date"] > link["status_date"]:
            if status not in {"Not yet due", "Ended before observation date", "Cannot be compared (promise)"}:
                errors.append(f"{where}: observation date is after the status date, so rule 3 applies")
        # Statements carry a quote and a statement basis.
        if status in {"Stated as reached", "Stated as not reached"}:
            if basis not in {"issuer statement", "reviewer statement"}:
                errors.append(f"{where}: a 'Stated as' label needs basis 'issuer statement' or 'reviewer statement'")
            if not link.get("statement_quote"):
                errors.append(f"{where}: a 'Stated as' label needs the statement quote")
        if status.startswith("Reported figure") and basis != "comparison of figures by the editor; no issuer statement found":
            errors.append(f"{where}: a comparison label needs the comparison basis")
        if status == "No report found by the editor" and "report not obtained" in link.get("flags", ""):
            errors.append(f"{where}: a report known but not obtained may never take 'No report found by the editor' (E.10.11)")
    for n, p in enumerate(tables.get("promises", []), start=2):
        if p.get("quote_language") and p["quote_language"] != "en" and not p.get("quote_translation_en"):
            errors.append(f"promises line {n}: non-English quote needs the English translation")
        if p.get("target_form") == "relative" and not p.get("baseline_period"):
            errors.append(f"promises line {n}: a relative target needs its baseline period")
    return errors


def scan_words() -> list:
    hits = []
    files = []
    for item in PROJECT_TEXT:
        path = ROOT / item
        if path.is_dir():
            files += [f for f in path.rglob("*") if f.suffix in {".md", ".html", ".txt"}]
        elif path.exists():
            files.append(path)
    for f in files:
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), start=1):
            if WORD_EXEMPT_LINE in line:
                continue
            # Text inside straight double quotes is quotation and is skipped.
            unquoted = re.sub(r'"[^"]*"', "", line).lower()
            for stem in WORD_STEMS:
                for m in re.finditer(stem, unquoted):
                    start = m.start()
                    # whole-word start only (so "unsafe" counts, "safeguard" is caught too: reword it)
                    if start == 0 or not unquoted[start - 1].isalpha() or stem in {"safe"}:
                        hits.append(f"{f.relative_to(ROOT)}:{n}: '{stem}' in: {line.strip()[:90]}")
    return hits


def load(name: str) -> list:
    path = ROOT / "data" / f"{name}.csv"
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    tables = {name: load(name) for name in SCHEMA["tables"]}
    errors = []
    for name, rows in tables.items():
        errors += check_table(name, rows)
    errors += check_rules(tables)
    if "--words" in sys.argv:
        errors += scan_words()
    for e in errors:
        print(e)
    print(f"{len(errors)} problem(s) found." if errors else "All checks passed.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
