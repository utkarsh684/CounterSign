"""Policy decision types and severity combiners."""

from enum import Enum


class PolicyOutcome(str, Enum):
    READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
    ESCALATE = "ESCALATE"
    DENY = "DENY"


class RuleDecision(str, Enum):
    PASS = "PASS"
    ESCALATE = "ESCALATE"
    DENY = "DENY"


def combine_decisions(policy_decision: PolicyOutcome, ai_risk_level: str) -> PolicyOutcome:
    """Combines deterministic policy output with independent AI security verifier output.

    CRITICAL SECURITY GUARANTEE:
    1. A deterministic DENY can NEVER be overridden by AI.
    2. AI can ONLY make the decision stricter (fail closed or escalate).
    3. AI is advisory and cannot approve transactions.
    """
    # Deterministic DENY is absolute
    if policy_decision == PolicyOutcome.DENY:
        return PolicyOutcome.DENY

    risk = ai_risk_level.upper()
    if risk in ["HIGH", "CRITICAL"]:
        return PolicyOutcome.ESCALATE

    if risk == "MEDIUM":
        return PolicyOutcome.ESCALATE

    # If policy is ESCALATE, it remains ESCALATE regardless of AI risk
    if policy_decision == PolicyOutcome.ESCALATE:
        return PolicyOutcome.ESCALATE

    # If policy is READY_FOR_APPROVAL and AI risk is LOW
    if risk == "LOW":
        return PolicyOutcome.READY_FOR_APPROVAL

    # Default fail closed to ESCALATE for any unrecognized state
    return PolicyOutcome.ESCALATE
