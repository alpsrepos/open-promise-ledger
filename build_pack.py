"""Build the document pack index for one issuer group (Method E.6, Appendix D).

Usage: python scripts/build_pack.py EVIDENCE_DIR GROUP_KEY OUT_DIR [--isins ISIN1;ISIN2] [--terms "metric 1;metric 2"] [--reserved FILE1;FILE2]

Files named in --reserved (a reservation against text and data mining or AI use, Method E.6) are
listed in no_ai.csv for the editor and never enter pack.csv.

Writes OUT_DIR/pack.csv (source_id, file, type, title, sha256, pages, page_range) and
OUT_DIR/frame-row.json (group_key, issuer and guarantor LEIs, Euronext labels from the
restricted frame files, which stay in this workspace).

Files over 100 pages are cut to the pages that hold a registered search term (Appendix D),
plus two pages either side (Method E.6); every other file is sent whole. The terms and the ranges are logged
in pack.csv, so the pack can be rebuilt and checked.
"""
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCH_TERMS = ["Sustainability Performance Target", "SPT", "Key Performance Indicator", "KPI",
                "Target Observation Date", "Observation Date", "Reference Date", "Reference Year",
                "Step Up", "Step-Up", "Premium", "Reporting", "Notification Deadline", "Recalculation",
                "Baseline"]
LONG = 100


def pages(path):
    try:
        out = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True).stdout
        return int(re.search(r"Pages:\s+(\d+)", out).group(1))
    except Exception:
        return 0


def page_text(path, n):
    return subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), "-layout", str(path), "-"],
                          capture_output=True, text=True).stdout


def ranges(nums):
    nums = sorted(set(nums))
    out, start, prev = [], None, None
    for n in nums:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append((start, prev))
            start = prev = n
    if start is not None:
        out.append((start, prev))
    return ";".join(f"{a}-{b}" if a != b else str(a) for a, b in out)


def hit_pages(path, n, terms):
    pats = [re.compile(r"\b" + re.escape(t) + r"\b", re.I) for t in terms]
    hits = []
    whole = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True).stdout
    for i, t in enumerate(whole.split("\f")[:n], start=1):
        if any(p.search(t) for p in pats):
            hits += [i - 2, i - 1, i, i + 1, i + 2]
    return [h for h in hits if 1 <= h <= n]


def frame_row(group_key):
    row = {"group_key": group_key}
    g = ROOT / "frame" / "frame-groups.csv"
    b = ROOT / "frame" / "frame-bonds.csv"
    if g.exists():
        for r in csv.DictReader(open(g, encoding="utf-8")):
            if r["group_key"] == group_key:
                row.update(r)
    if b.exists():
        row["frame_bonds"] = [r for r in csv.DictReader(open(b, encoding="utf-8")) if r.get("group_key") == group_key]
    return row


def main(a):
    ev, gk, out = Path(a[0]), a[1], Path(a[2])
    isins = a[a.index("--isins") + 1].split(";") if "--isins" in a else []
    extra = a[a.index("--terms") + 1].split(";") if "--terms" in a else []
    terms = SEARCH_TERMS + extra + isins
    out.mkdir(parents=True, exist_ok=True)
    reserved = set(a[a.index("--reserved") + 1].split(";")) if "--reserved" in a else set()
    allf = sorted(f for f in ev.rglob("*") if f.is_file() and f.suffix.lower() in {".pdf", ".html", ".xhtml", ".htm"}
                  and "ocr" not in f.parts)
    files = [f for f in allf if f.name not in reserved]
    with open(out / "no_ai.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "sha256", "reason"])
        for f in allf:
            if f.name in reserved:
                w.writerow([str(f), hashlib.sha256(f.read_bytes()).hexdigest(), "reservation found: not sent to AI"])
    rows = []
    for i, f in enumerate(files, start=1):
        n = pages(f) if f.suffix.lower() == ".pdf" else 0
        pr = "all"
        if n > LONG:
            pr = ranges(hit_pages(f, n, terms)) or "none found"
        rows.append({"source_id": f"S-{i}", "file": str(f), "type": "", "title": f.stem,
                     "sha256": hashlib.sha256(f.read_bytes()).hexdigest(), "pages": n, "page_range": pr})
    with open(out / "pack.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (out / "frame-row.json").write_text(json.dumps(frame_row(gk), indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "pack-terms.txt").write_text("\n".join(terms), encoding="utf-8")
    print(f"{len(rows)} files; pack index in {out / 'pack.csv'}; fill 'type' (document type) by hand")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(sys.argv[1:])
