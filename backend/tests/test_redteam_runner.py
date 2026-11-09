"""Unit tests for the 18 Red-Team Arena and Benign Scenarios."""

import pytest
from app.redteam.scenarios import SCENARIOS, run_scenario


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if s["type"] == "ATTACK"], ids=lambda s: s["id"])
def test_all_attacks_blocked_and_never_reach_paypal(scenario):
    res = run_scenario(scenario["id"])
    assert res.reached_paypal is False, f"CRITICAL: Scenario {scenario['id']} reached PayPal execution!"
    assert res.final_decision in ["BLOCKED", "ESCALATE", "DENY"], f"Attack {scenario['id']} was not blocked or escalated!"


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if s["type"] == "BENIGN"], ids=lambda s: s["id"])
def test_all_benign_scenarios_handled_properly(scenario):
    res = run_scenario(scenario["id"])
    assert res.final_decision in ["READY_FOR_APPROVAL", "ESCALATE"], f"Benign {scenario['id']} was improperly rejected!"
