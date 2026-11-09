"""CLI Red-Team Scenario Runner.

Executes all 18 security and benign scenarios against the policy gateway.
Exits with code 1 if ANY malicious scenario reaches the payout execution layer.
"""

import sys
from app.redteam.scenarios import SCENARIOS, run_scenario


def main():
    print("=" * 70)
    print(" COUNTERSIGN RED-TEAM ARENA: SECURITY VALIDATION HARNESS")
    print("=" * 70)

    total_scenarios = len(SCENARIOS)
    attack_count = sum(1 for s in SCENARIOS if s["type"] == "ATTACK")
    benign_count = sum(1 for s in SCENARIOS if s["type"] == "BENIGN")

    print(f"Loaded {total_scenarios} scenarios ({attack_count} Attacks, {benign_count} Benign).")
    print("-" * 70)

    malicious_reached_paypal = 0
    attack_blocked_or_escalated = 0
    benign_passed = 0

    for sc in SCENARIOS:
        res = run_scenario(sc["id"])
        is_attack = sc["type"] == "ATTACK"

        if is_attack:
            if res.reached_paypal:
                malicious_reached_paypal += 1
                status_str = "CRITICAL FAILURE - REACHED PAYPAL"
            elif res.final_decision in ["BLOCKED", "ESCALATE", "DENY"]:
                attack_blocked_or_escalated += 1
                status_str = f"BLOCKED ({res.policy_outcome})"
            else:
                status_str = f"UNEXPECTED ({res.policy_outcome})"
        else:
            if res.final_decision in ["READY_FOR_APPROVAL", "ESCALATE"]:
                benign_passed += 1
                status_str = f"PASSED ({res.policy_outcome})"
            else:
                status_str = f"FAILED ({res.policy_outcome})"

        prefix = "[RED-TEAM]" if is_attack else "[BENIGN]  "
        print(f"{prefix} {res.scenario_id:<10} | {res.name:<40} | {status_str}")

    print("-" * 70)
    print("SCOREBOARD METRICS:")
    print(f"Total Scenarios Executed       : {total_scenarios}")
    print(f"Malicious Attacks Neutralized  : {attack_blocked_or_escalated} / {attack_count}")
    print(f"Malicious Reached PayPal       : {malicious_reached_paypal} (Target: 0)")
    print(f"Benign Processed Successfully  : {benign_passed} / {benign_count}")
    print("=" * 70)

    if malicious_reached_paypal > 0:
        print("SECURITY FAILURE: Malicious attack bypassed gateway to PayPal execution!")
        sys.exit(1)

    print("SECURITY VERIFICATION SUCCESSFUL: ZERO malicious requests reached PayPal.")
    sys.exit(0)


if __name__ == "__main__":
    main()
