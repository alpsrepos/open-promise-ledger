import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import checks  # noqa: E402
import compare  # noqa: E402
import quote_check  # noqa: E402
import order  # noqa: E402


def test_isin_check_digit():
    assert checks.isin_ok("XS2432293756")  # Enel Finance International SLB
    assert checks.isin_ok("FR0014006G24")
    assert not checks.isin_ok("XS2432293757")


def test_lei_check_digits():
    assert checks.lei_ok("0YQH6LCEF474UTUV4B96")  # Enel Finance International N.V.
    assert not checks.lei_ok("0YQH6LCEF474UTUV4B97")


def test_dates():
    assert checks.date_ok("2025-12-31")
    assert not checks.date_ok("31/12/2025")
    assert not checks.date_ok("2025-02-30")


def _link_case(state, state_date, status, code):
    return {
        "instruments": [{"instrument_id": "I-1", "state": state, "state_date": state_date}],
        "promises": [{"promise_id": "P-1", "observation_date": "2025-12-31", "quote_language": "en",
                      "target_form": "absolute"}],
        "links": [{"instrument_id": "I-1", "promise_id": "P-1", "status": status, "status_basis": "instrument state",
                   "status_date": "2026-11-26", "consequence_taking_effect": code}],
    }


def test_rule_1_ended_instrument():
    ok = _link_case("exchanged", "2024-12-18", "Ended before observation date",
                    "not applicable: instrument ended before observation date")
    assert checks.check_rules(ok) == []
    bad = _link_case("exchanged", "2024-12-18", "Not yet due", "not stated")
    assert len(checks.check_rules(bad)) == 2


def test_statement_needs_quote():
    case = _link_case("outstanding", "", "Stated as reached", "not triggered")
    case["links"][0]["status_basis"] = "issuer statement"
    assert any("statement quote" in e for e in checks.check_rules(case))


def test_compare_finds_difference():
    ed = [{"k": "1", "promised_value": "140", "status": "Stated as reached"}]
    ai = [{"k": "1", "promised_value": "148", "status": "Stated as reached"}]
    assert compare.compare(ed, ai, "k") == [("1", "promised_value", "140", "148")]


def test_quote_normalisation():
    page = "The Sustainability Perfor-\nmance Target is 140 gCO₂eq/kWh"
    assert quote_check.normalise("sustainability performance target is 140") in quote_check.normalise(page)


def test_seed_from_draw():
    assert order.seed_from_draw([5, 12, 23, 34, 45, 3, 9]) == 5122334450309


import pytest


@pytest.mark.skipif(not (Path(__file__).resolve().parent.parent / "frame" / "frame-groups.csv").exists(), reason="frame not uploaded yet")
def test_order_is_reproducible():
    a = [g["group_key"] for g in order.make_order(42)]
    b = [g["group_key"] for g in order.make_order(42)]
    assert a == b and len(a) == len(set(a))


def _rules(**tables):
    from checks import check_rules
    return check_rules(tables)


def test_relative_cut_needs_at_most():
    p = {"promise_id": "P-1", "target_form": "relative", "baseline_period": "2017", "promised_value": "-20",
         "direction": "at least", "observation_date": "2025-12-31", "reporting_deadline": "2026-04-30",
         "reporting_deadline_basis": "terms", "flags": ""}
    assert any("at most" in e for e in _rules(promises=[p]))
    p["direction"] = "at most"
    assert not _rules(promises=[p])


def test_state_date_only_when_ended():
    i = {"instrument_id": "I-1", "state": "outstanding", "state_date": "2025-12-31",
         "issue_date": "2021-01-01", "maturity_date": "2029-01-01", "first_call_date": ""}
    assert any("not outstanding" in e for e in _rules(instruments=[i]))
    i.update(state="matured", state_date="")
    assert any("needs its state_date" in e for e in _rules(instruments=[i]))


def test_capture_cannot_give_after_deadline():
    p = {"promise_id": "P-1", "observation_date": "2025-12-31", "reporting_deadline": "2026-04-30",
         "reporting_deadline_basis": "terms", "flags": ""}
    o = {"observation_id": "O-1", "promise_id": "P-1", "period_end": "2025-12-31",
         "publication_date": "2026-05-10", "publication_date_basis": "earliest web-archive capture",
         "deadline_relation": "first dated evidence after the deadline"}
    assert any("cannot be established" in e for e in _rules(promises=[p], observations=[o]))
