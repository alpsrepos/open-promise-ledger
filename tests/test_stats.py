import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from stats import clopper_pearson, krippendorff_alpha_nominal, gwet_ac1, cluster_bootstrap_share


def test_clopper_pearson_known_values():
    lo, hi = clopper_pearson(9, 10)
    assert abs(lo - 0.5550) < 1e-3 and abs(hi - 0.9975) < 1e-3
    assert clopper_pearson(0, 10)[0] == 0.0 and clopper_pearson(10, 10)[1] == 1.0


def test_alpha_perfect_and_textbook():
    assert krippendorff_alpha_nominal([["a", "a"], ["b", "b"], ["a", "a"]]) == 1.0
    # Krippendorff (2011) nominal example: alpha = 0.743 for the 4-coder reliability data
    data = [[1, 1, None, 1], [2, 2, 3, 2], [3, 3, 3, 3], [3, 3, 3, 3], [2, 2, 2, 2], [1, 2, 3, 4],
            [4, 4, 4, 4], [1, 1, 2, 1], [2, 2, 2, 2], [None, 5, 5, 5], [None, None, 1, 1], [None, None, 3, None]]
    assert abs(krippendorff_alpha_nominal(data) - 0.743) < 1e-3


def test_ac1_and_bootstrap():
    assert gwet_ac1(list("aaab"), list("aaab")) == 1.0
    est, lo, hi = cluster_bootstrap_share({"g1": ["x", "y"], "g2": ["x"], "g3": ["y", "y"]}, "x", reps=2000)
    assert abs(est - 0.4) < 1e-9 and lo <= est <= hi
