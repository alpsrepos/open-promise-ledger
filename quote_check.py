"""Quote check (Method E.6): is each quote on its cited page?

Input: a CSV with columns source_file, page, quote, and optionally ocr_file (one row per value).
Or: python scripts/quote_check.py --record RECORD_DIR EVIDENCE_DIR, which reads every quote in the
record's tables (promises, links, observations), finds each source file in EVIDENCE_DIR by the
sha256 in sources.csv, and checks it.

Pages are 1-based PDF pages. Text is normalised: ligatures, hyphenation at line ends, quotes,
line breaks and repeated spaces. Each page is read three ways (pypdf, pdftotext -layout,
pdftotext -raw), so two-column layouts do not cause false failures. For image pages, the OCR text
(EVIDENCE_DIR/ocr/<file stem>-<page>.txt, or the ocr_file column) is matched with a tolerance;
such a pass is printed "found (OCR)" and the editor reads the page image.
A figure from a table is quoted as its parts joined by " | " (row label | column label | cell);
each part must be on the page. A pass shows only that the quote exists on that page, not that the value is right.
"""
import csv
import difflib
import hashlib
import re
import subprocess
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "­": ""}
OCR_TOLERANCE = 0.90


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    for k, v in LIGATURES.items():
        text = text.replace(k, v)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = (text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
            .replace("–", "-").replace("—", "-"))
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


@lru_cache(maxsize=None)
def page_texts(path: str, page: int) -> tuple:
    out = []
    try:
        from pypdf import PdfReader
        out.append(PdfReader(path).pages[page - 1].extract_text() or "")
    except Exception:
        pass
    for mode in ("-layout", "-raw"):
        try:
            r = subprocess.run(["pdftotext", mode, "-f", str(page), "-l", str(page), path, "-"],
                               capture_output=True, text=True, timeout=60)
            out.append(r.stdout)
        except Exception:
            pass
    return tuple(normalise(t) for t in out)


def fuzzy_in(quote: str, text: str) -> float:
    if not quote or not text:
        return 0.0
    n = len(quote)
    best = 0.0
    step = max(1, n // 4)
    for i in range(0, max(1, len(text) - n + 1), step):
        window = text[i:i + n + n // 5]
        r = difflib.SequenceMatcher(None, quote, window).find_longest_match(0, len(quote), 0, len(window))
        if r.size < n * 0.3:
            continue
        best = max(best, difflib.SequenceMatcher(None, quote, window[:n + n // 10]).ratio())
        if best >= 0.99:
            break
    return best


def check(source_file: str, page: int, quote: str, ocr_file: str = "") -> str:
    q = normalise(quote)
    q = q.replace("...", " ").replace("…", " ")
    parts = [p.strip() for p in re.split(r"\s{2,}|\s\|\s", q) if p.strip()] or [q]
    texts = page_texts(source_file, page) if source_file.lower().endswith(".pdf") else (
        normalise(Path(source_file).read_text(encoding="utf-8", errors="ignore")),)
    if all(any(p in t for t in texts) for p in parts):
        return "found"
    # A hyphenated word broken at a line end ("Step-\nUp") loses its hyphen in normalising;
    # compare once more with every hyphen removed on both sides.
    nh = lambda s: s.replace("-", "")
    if all(any(nh(p) in nh(t) for t in texts) for p in parts):
        return "found"
    if ocr_file and Path(ocr_file).exists():
        ocr = normalise(Path(ocr_file).read_text(encoding="utf-8", errors="ignore"))
        if all(p in ocr for p in parts):
            return "found (OCR)"
        score = min(fuzzy_in(p, ocr) for p in parts)
        if score >= OCR_TOLERANCE:
            return f"found (OCR, {score:.2f})"
    return "UNSUPPORTED"


def rows_from_record(record: Path, evidence: Path):
    files = {}
    for f in evidence.rglob("*"):
        if f.is_file() and f.suffix.lower() in {".pdf", ".html", ".xhtml", ".htm"}:
            files[hashlib.sha256(f.read_bytes()).hexdigest()] = f
    src = {}
    with open(record / "sources.csv", encoding="utf-8") as fh:
        for s in csv.DictReader(fh):
            src[s["source_id"]] = files.get(s.get("sha256", ""))
    specs = [("promises.csv", "quote_original", "quote_source_id", "quote_page"),
             ("observations.csv", "value_quote", "source_id", "page")]
    for table, qf, sf, pf in specs:
        p = record / table
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get(qf) and r.get(sf) and str(r.get(pf, "")).isdigit():
                    f = src.get(r[sf])
                    ocr = evidence / "ocr" / f"{f.stem}-{r[pf]}.txt" if f else None
                    yield {"source_file": str(f) if f else "", "page": r[pf], "quote": r[qf],
                           "ocr_file": str(ocr) if ocr else "", "where": f"{table} {r[sf]} p.{r[pf]}"}


def main() -> int:
    a = sys.argv[1:]
    if a and a[0] == "--record":
        rows = list(rows_from_record(Path(a[1]), Path(a[2])))
    elif len(a) == 1:
        with open(a[0], newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    else:
        sys.exit(__doc__)
    failed = 0
    for row in rows:
        if not row.get("source_file"):
            result = "UNSUPPORTED (source file not found by hash)"
        else:
            result = check(row["source_file"], int(row["page"]), row["quote"], row.get("ocr_file", ""))
        if result.startswith("UNSUPPORTED"):
            failed += 1
        print(f"{result:<22} {row.get('where', row['source_file'] + ' p.' + str(row['page']))}  {row['quote'][:60]}")
    print(f"{failed} unsupported quote(s) of {len(rows)}.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
