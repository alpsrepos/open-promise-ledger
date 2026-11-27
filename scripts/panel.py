"""Check panel helpers (Method E.6): blinding, comparison and planted-error tests.

Usage:
  python scripts/panel.py blind RECORD_DIR OUT_DIR
      Copies the record with every status-bearing field removed, for the blind status check.
  python scripts/panel.py compare-status RECORD_DIR BLIND_RESULT.csv
      Compares a blind status result (columns link_id,status,status_basis,consequence_taking_effect)
      with the record.
  python scripts/panel.py compare-reading RECORD_DIR BLIND_ITEMS.csv
      BLIND_ITEMS.csv has columns kind,value,file,page,quote. Lists numbers and dates the blind
      reader found that appear nowhere in the record (possible omissions), and core numbers and
      dates in the record that the blind reader did not find (possible unsupported values).
  python scripts/panel.py plant RECORD_DIR OUT_DIR KEY_DIR [N] [SEED]
      Makes a copy of the record with N planted errors (default 6); the key goes to KEY_DIR,
      which no checker may read. Used to measure what the panel catches.
  python scripts/panel.py score KEY_DIR FINDINGS.csv
      FINDINGS.csv has columns table,row_id,field (one line per finding). Prints planted errors
      caught and missed.
"""
import csv
import json
import random
import re
import shutil
import sys
from pathlib import Path

TABLES = ["instruments", "promises", "links", "observations"]
BLIND_FIELDS = {
    "links": ["status", "status_basis", "status_date", "statement_quote", "statement_source_id",
              "consequence_taking_effect", "consequence_announced_date", "flags"],
    "observations": ["statement_text", "deadline_relation"],
    "promises": ["flags", "change_history"],
    "instruments": ["flags"],
}
ID = {"instruments": "instrument_id", "promises": "promise_id", "links": "link_id", "observations": "observation_id"}
TOKEN = re.compile(r"\d{4}-\d{2}-\d{2}|-?\d[\d,]*\.?\d*")


def read(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def blind(record, out):
    out.mkdir(parents=True, exist_ok=True)
    for t in TABLES:
        rows = read(record / f"{t}.csv")
        for r in rows:
            for f in BLIND_FIELDS.get(t, []):
                if f in r:
                    r[f] = ""
        write(out / f"{t}.csv", rows)
    shutil.copy(record / "sources.csv", out / "sources.csv")
    print(f"blinded copy in {out}; NOTES.md and check files are not copied")


def compare_status(record, result):
    rec = {r["link_id"]: r for r in read(record / "links.csv")}
    diffs = 0
    for b in read(result):
        r = rec.get(b["link_id"])
        if r is None:
            print(f"{b['link_id']}: not in the record")
            diffs += 1
            continue
        for f in ["status", "status_basis", "consequence_taking_effect"]:
            if b.get(f, "").strip() != r.get(f, "").strip():
                print(f"{b['link_id']} {f}: record '{r.get(f)}' / blind '{b.get(f)}'")
                diffs += 1
    print(f"{diffs} difference(s)")
    return diffs


def tokens(text):
    out = set()
    for m in TOKEN.findall(text or ""):
        m = m.replace(",", "").rstrip(".")
        if m and m not in {"-", "0"} and not re.fullmatch(r"-?\d", m):
            out.add(m.lstrip("+"))
    return out


def compare_reading(record, items):
    rec_text = ""
    core = set()
    for t in TABLES:
        for r in read(record / f"{t}.csv"):
            rec_text += " ".join(r.values()) + " "
            for f in ["promised_value", "baseline_value", "observation_date", "reporting_deadline",
                      "reported_value", "maturity_date", "issue_date", "amount_million", "period_end"]:
                core |= tokens(r.get(f, ""))
    notes = record / "NOTES.md"
    if notes.exists():
        rec_text += notes.read_text(encoding="utf-8")
    rec_tokens = tokens(rec_text)
    blind_tokens = {}
    for it in read(items):
        for tok in tokens(it.get("value", "")):
            blind_tokens.setdefault(tok, it)
    missing = {k: v for k, v in blind_tokens.items() if k not in rec_tokens}
    unsupported = sorted(core - set(blind_tokens))
    print("Found by the blind reader, absent from the record (possible omissions):")
    for k, it in sorted(missing.items()):
        print(f"  {k}: {it.get('kind')} ({it.get('file')} p.{it.get('page')})")
    print("Core values in the record the blind reader did not find (check at the page):")
    for k in unsupported:
        print(f"  {k}")
    return missing, unsupported


def plant(record, out, keydir, n=6, seed=1):
    rnd = random.Random(seed)
    shutil.copytree(record, out, dirs_exist_ok=True)
    for p in out.iterdir():
        if p.suffix == ".md":
            p.unlink()  # notes hold the true values; checkers work from the tables and the evidence
    data = {t: read(out / f"{t}.csv") for t in TABLES}
    kinds = ["number", "date", "page", "direction", "status", "isin_digit"]
    key = []
    tries = 0
    while len(key) < n and tries < 500:
        tries += 1
        kind = kinds[len(key) % len(kinds)] if len(key) < len(kinds) else rnd.choice(kinds)
        t = rnd.choice(TABLES)
        rows = data[t]
        if not rows:
            continue
        r = rnd.choice(rows)
        fields = list(r.keys())
        rnd.shuffle(fields)
        done = False
        for f in fields:
            v = r[f]
            if not v or f in {ID[t], "promise_id", "instrument_id"}:
                continue
            new = None
            if kind == "number" and f in {"promised_value", "baseline_value", "reported_value", "amount_million"}:
                m = re.search(r"\d+", v)
                if m:
                    d = int(m.group()) + rnd.choice([1, 2, 5, 10])
                    new = v[:m.start()] + str(d) + v[m.end():]
            elif kind == "date" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) and f != "status_date":
                y = int(v[:4]) + rnd.choice([-1, 1])
                new = f"{y}{v[4:]}"
            elif kind == "page" and f in {"quote_page", "page"} and v.isdigit():
                new = str(int(v) + rnd.choice([1, 2, -1]))
            elif kind == "direction" and f == "direction":
                new = {"at least": "at most", "at most": "at least", "equal": "at least"}[v]
            elif kind == "status" and f == "status":
                new = {"Stated as reached": "Stated as not reached", "Stated as not reached": "Stated as reached"}.get(v)
            elif kind == "isin_digit" and f == "isins":
                i = rnd.randrange(2, len(v.split(";")[0]) - 1)
                c = v[i]
                if c.isdigit():
                    new = v[:i] + str((int(c) + 1) % 10) + v[i + 1:]
            if new and new != v:
                key.append({"table": t, "row_id": r[ID[t]], "field": f, "kind": kind, "true": v, "planted": new})
                r[f] = new
                done = True
                break
        if not done:
            continue
    for t in TABLES:
        write(out / f"{t}.csv", data[t])
    keydir.mkdir(parents=True, exist_ok=True)
    (keydir / "key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(f"{len(key)} errors planted in {out}; key in {keydir} (not for checkers)")


def score(keydir, findings):
    key = json.loads((keydir / "key.json").read_text(encoding="utf-8"))
    found = {(f["table"], f["row_id"], f["field"]) for f in read(findings)}
    caught = [k for k in key if (k["table"], k["row_id"], k["field"]) in found]
    for k in key:
        mark = "caught" if k in caught else "MISSED"
        print(f"{mark}: {k['kind']} {k['table']} {k['row_id']} {k['field']}: {k['true']} -> {k['planted']}")
    print(f"caught {len(caught)} of {len(key)}")
    return len(caught), len(key)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(1)
    cmd = a[0]
    if cmd == "blind":
        blind(Path(a[1]), Path(a[2]))
    elif cmd == "compare-status":
        sys.exit(1 if compare_status(Path(a[1]), Path(a[2])) else 0)
    elif cmd == "compare-reading":
        compare_reading(Path(a[1]), Path(a[2]))
    elif cmd == "plant":
        plant(Path(a[1]), Path(a[2]), Path(a[3]), int(a[4]) if len(a) > 4 else 6, int(a[5]) if len(a) > 5 else 1)
    elif cmd == "score":
        score(Path(a[1]), Path(a[2]))
    else:
        print(__doc__)
        sys.exit(1)
