"""Print the hashes that the protocol registration records (Method section 8).

Usage: python scripts/freeze.py > protocol/frozen-hashes.txt
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ["METHOD.md", "protocol/extraction-prompt.md", "dictionary/schema.json", "dictionary/data-dictionary.md",
         "scripts/checks.py", "scripts/quote_check.py", "scripts/readings.py", "scripts/compare.py",
         "scripts/panel.py", "scripts/stats.py", "scripts/order.py", "scripts/build_pack.py",
         "scripts/build_frame.py", "scripts/notice.py", "coder/CODER-INSTRUCTIONS.md",
         "auditor/AUDITOR-INSTRUCTIONS.md"]
for f in FILES:
    p = ROOT / f
    print(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {f}" if p.exists() else f"MISSING  {f}")
