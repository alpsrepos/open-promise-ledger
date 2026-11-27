"""Release statistics (Method section 7, Appendix D, Appendix E.7).

Usage:
  python scripts/stats.py counts DATA_DIR [--exclude-groups G1,G2]
      Plain counts by status, per link and per promise (a promise takes the status of its links
      when they agree, otherwise "mixed"), with the 270-day deadline and the 365-day sensitivity.
  python scripts/stats.py validation KEY.csv AI.csv
      KEY.csv and AI.csv have columns unit_id,field,value (unit_id is a promise id; field a core
      field). Prints recall, accuracy and invented values as "x of n" with exact 95% intervals.

Functions are also imported by tests: clopper_pearson, krippendorff_alpha_nominal, gwet_ac1,
cluster_bootstrap_share.
"""
import csv
import datetime as dt
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

from scipy.stats import beta

CORE_FIELDS = ["metric", "unit", "direction", "baseline_value", "baseline_period", "promised_value",
               "observation_date", "reporting_deadline", "reported_value", "status", "consequence_taking_effect"]


def clopper_pearson(x, n, level=0.95):
    """Exact two-sided interval for x successes in n trials."""
    if n == 0:
        return (float("nan"), float("nan"))
    a = (1 - level) / 2
    lo = 0.0 if x == 0 else beta.ppf(a, x, n - x + 1)
    hi = 1.0 if x == n else beta.ppf(1 - a, x + 1, n - x)
    return (float(lo), float(hi))


def x_of_n(x, n):
    lo, hi = clopper_pearson(x, n)
    return f"{x} of {n} (95% exact interval {lo:.2f} to {hi:.2f})"


def krippendorff_alpha_nominal(units):
    """units: list of lists, the values coders gave one unit (None for missing). Nominal alpha."""
    pairs = Counter()
    for vals in units:
        vals = [v for v in vals if v is not None]
        m = len(vals)
        if m < 2:
            continue
        for i, a in enumerate(vals):
            for j, b in enumerate(vals):
                if i != j:
                    pairs[(a, b)] += 1 / (m - 1)
    n_c = Counter()
    for (a, _b), w in pairs.items():
        n_c[a] += w
    n = sum(n_c.values())
    if n <= 1:
        return float("nan")
    d_o = sum(w for (a, b), w in pairs.items() if a != b) / n
    d_e = sum(n_c[a] * n_c[b] for a in n_c for b in n_c if a != b) / (n * (n - 1))
    return 1.0 if d_e == 0 else 1 - d_o / d_e


def gwet_ac1(a, b):
    """Gwet's AC1 for two raters over the same items (nominal)."""
    assert len(a) == len(b) and a
    n = len(a)
    cats = sorted(set(a) | set(b))
    q = len(cats)
    pa = sum(x == y for x, y in zip(a, b)) / n
    if q < 2:
        return 1.0
    pi = {c: (a.count(c) + b.count(c)) / (2 * n) for c in cats}
    pe = sum(p * (1 - p) for p in pi.values()) / (q - 1)
    return 1.0 if pe == 1 else (pa - pe) / (1 - pe)


def cluster_bootstrap_share(groups, label, reps=10000, seed=1):
    """groups: dict group -> list of status labels. Share of `label` with a percentile 95% interval
    from resampling groups with replacement."""
    keys = list(groups)
    rnd = random.Random(seed)

    def share(ks):
        tot = sum(len(groups[k]) for k in ks)
        return sum(groups[k].count(label) for k in ks) / tot if tot else float("nan")

    est = share(keys)
    sims = sorted(share([rnd.choice(keys) for _ in keys]) for _ in range(reps))
    return est, sims[int(0.025 * reps)], sims[int(0.975 * reps) - 1]


def read(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def counts(data, exclude=()):
    promises = {p["promise_id"]: p for p in read(data / "promises.csv")}
    links = [l for l in read(data / "links.csv")]
    if exclude:
        links = [l for l in links if promises.get(l["promise_id"], {}).get("group_key") not in exclude]
    by_link = Counter(l["status"] for l in links)
    per_promise = defaultdict(set)
    for l in links:
        per_promise[l["promise_id"]].add(l["status"])
    by_promise = Counter(next(iter(s)) if len(s) == 1 else "mixed" for s in per_promise.values())
    print(f"Links: {len(links)}; promises: {len(per_promise)}; groups: "
          f"{len({promises[p]['group_key'] for p in per_promise if p in promises})}")
    print("Status, per link, per promise:")
    for s in sorted(set(by_link) | set(by_promise)):
        print(f"  {s}: {by_link.get(s, 0)} of {len(links)} links; {by_promise.get(s, 0)} of {len(per_promise)} promises")
    # 365-day sensitivity: only promises whose deadline came from the 270-day fallback can change.
    moved = 0
    for pid, p in promises.items():
        if p.get("reporting_deadline_basis") == "fallback 270 days" and p.get("observation_date"):
            d365 = dt.date.fromisoformat(p["observation_date"]) + dt.timedelta(days=365)
            moved += 1
            print(f"  365-day check: {pid} deadline would be {d365.isoformat()} (recompute its status by rule)")
    if not moved:
        print("  365-day check: no promise uses the fallback deadline; counts unchanged")


def validation(key_path, ai_path):
    key = defaultdict(dict)
    for r in read(key_path):
        key[r["unit_id"]][r["field"]] = r["value"].strip()
    ai = defaultdict(dict)
    for r in read(ai_path):
        ai[r["unit_id"]][r["field"]] = r["value"].strip()
    found = [u for u in key if u in ai]
    print("Recall (key promises the AI found):", x_of_n(len(found), len(key)))
    match = total = invented = inv_n = 0
    for u in found:
        for f, v in ai[u].items():
            if f in key[u]:
                total += 1
                match += v == key[u][f]
            else:
                inv_n += 1
                invented += 1
    print("Accuracy (AI core values equal to the key):", x_of_n(match, total))
    extra = [u for u in ai if u not in key]
    print(f"Invented values: {invented} values in fields the key leaves empty; {len(extra)} promises not in the key")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(1)
    if a[0] == "counts":
        ex = ()
        if "--exclude-groups" in a:
            ex = set(a[a.index("--exclude-groups") + 1].split(","))
        counts(Path(a[1]), ex)
    elif a[0] == "validation":
        validation(Path(a[1]), Path(a[2]))
    else:
        print(__doc__)
        sys.exit(1)
