"""Random order of issuer groups (Method section 3 and Appendix D).

The groups in frame/frame-groups.csv are sorted by group key (parent LEI), then shuffled
with Python's random.Random(seed).shuffle. The seed is a public number fixed after the
frame is registered: the main numbers and stars of the first EuroMillions draw after the
frame deposit, written as one integer in draw order (for example 5 12 23 34 45 + 3 9 ->
5122334450309 with each number written as two digits).

Run: python scripts/order.py SEED
Writes frame/order.csv and prints its SHA-256.
"""
import csv
import hashlib
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def seed_from_draw(numbers: list) -> int:
    return int("".join(f"{n:02d}" for n in numbers))


def make_order(seed: int) -> list:
    with open(ROOT / "frame" / "frame-groups.csv", newline="", encoding="utf-8") as fh:
        groups = sorted(csv.DictReader(fh), key=lambda r: r["group_key"])
    rng = random.Random(seed)
    rng.shuffle(groups)
    return groups


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/order.py SEED")
    seed = int(sys.argv[1])
    groups = make_order(seed)
    out = ROOT / "frame" / "order.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["position", "group_key", "group_name", "group_country", "bonds", "bonds_listed_by_2023"])
        for pos, g in enumerate(groups, start=1):
            writer.writerow([pos, g["group_key"], g["group_name"], g["group_country"], g["bonds"], g["bonds_listed_by_2023"]])
    print(f"seed {seed}; python {sys.version.split()[0]}; random.Random.shuffle")
    print("sha256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
