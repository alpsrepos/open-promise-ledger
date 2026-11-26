"""Quote check (Method E.6): is each quote on its cited page?

Input: a CSV with columns source_file, page, quote (one row per value the AI or the editor gave).
Pages are 1-based. Text is normalised: ligatures, hyphenation at line ends, line breaks and
repeated spaces. A pass shows only that the quote exists on that page, not that the value is right.

Run: python scripts/quote_check.py quotes.csv  (needs: pip install pypdf)
"""
import csv
import re
import sys
import unicodedata

LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "­": ""}


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    for k, v in LIGATURES.items():
        text = text.replace(k, v)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)  # hyphenation at line end
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def page_text(path: str, page: int) -> str:
    from pypdf import PdfReader
    reader = PdfReader(path)
    return reader.pages[page - 1].extract_text() or ""


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/quote_check.py quotes.csv")
    failed = 0
    with open(sys.argv[1], newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            ok = normalise(row["quote"]) in normalise(page_text(row["source_file"], int(row["page"])))
            if not ok:
                failed += 1
            print(("found      " if ok else "UNSUPPORTED"), row["source_file"], row["page"], row["quote"][:70])
    print(f"{failed} unsupported quote(s).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
