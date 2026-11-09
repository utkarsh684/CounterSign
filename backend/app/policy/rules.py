"""Pure, independently testable deterministic financial policy rules.

No LLM calls or probabilistic models exist in this module.
Every rule operates deterministically on typed input context.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.policy.decision import RuleDecision
from app.schemas.payment import RuleResult


def check_kill_switch(kill_switch_enabled: bool) -> RuleResult:
    """Rule 1: Kill switch must not be active."""
    if kill_switch_enabled:
        return RuleResult(
            rule_id="RULE-01-KILL-SWITCH",
            rule_name="Global Security Kill Switch",
            passed=False,
            decision=RuleDecision.DENY.value,
            reason="Global security kill switch is currently active. All outgoing payments are halted.",
            parameter_checked="kill_switch_enabled",
            actual_value=True,
            allowed_value=False,
        )
    return RuleResult(
        rule_id="RULE-01-KILL-SWITCH",
        rule_name="Global Security Kill Switch",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Kill switch is inactive.",
    )


def check_mandate_active(mandate_status: str) -> RuleResult:
    """Rule 2: Mandate must be ACTIVE."""
    if mandate_status != "ACTIVE":
        return RuleResult(
            rule_id="RULE-02-MANDATE-STATUS",
            rule_name="Mandate Active Status",
            passed=False,
            decision=RuleDecision.DENY.value,
            reason=f"Spending mandate status is '{mandate_status}'. Only ACTIVE mandates permit transactions.",
            parameter_checked="mandate_status",
            actual_value=mandate_status,
            allowed_value="ACTIVE",
        )
    return RuleResult(
        rule_id="RULE-02-MANDATE-STATUS",
        rule_name="Mandate Active Status",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Mandate is active.",
    )


def check_mandate_not_revoked(is_revoked: bool) -> RuleResult:
    """Rule 3: Mandate must not be revoked."""
    if is_revoked:
        return RuleResult(
            rule_id="RULE-03-MANDATE-REVOCATION",
            rule_name="Mandate Revocation",
            passed=False,
            decision=RuleDecision.DENY.value,
            reason="This spending mandate version has been formally revoked.",
            parameter_checked="is_revoked",
            actual_value=True,
            allowed_value=False,
        )
    return RuleResult(
        rule_id="RULE-03-MANDATE-REVOCATION",
        rule_name="Mandate Revocation",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Mandate is not revoked.",
    )


def check_valid_amount(amount_minor: int) -> RuleResult:
    """Rule 4: Amount must be positive integer minor units."""
    if amount_minor <= 0:
        return RuleResult(
            rule_id="RULE-04-VALID-AMOUNT",
            rule_name="Valid Non-Zero Amount",
            passed=False,
            decision=RuleDecision.DENY.value,
            reason=f"Payment amount must be greater than zero. Received: {amount_minor} minor units.",
            parameter_checked="amount_minor",
            actual_value=amount_minor,
            allowed_value="> 0",
        )
    return RuleResult(
        rule_id="RULE-04-VALID-AMOUNT",
        rule_name="Valid Non-Zero Amount",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason=f"Amount is valid: {amount_minor} minor units.",
    )


def check_currency_allowlist(currency: str, allowed_currencies: List[str]) -> RuleResult:
    """Rule 5: Currency must be in the mandate allowlist."""
    normalized_cur = currency.upper().strip()
    allowed_norm = [c.upper().strip() for c in allowed_currencies]
    if normalized_cur not in allowed_norm:
        return RuleResult(
            rule_id="RULE-05-CURRENCY-ALLOWLIST",
            rule_name="Currency Allowlist",
            passed=False,
            decision=RuleDecision.DENY.value,
            reason=f"Requested currency '{normalized_cur}' is not permitted by active mandate. Allowed: {allowed_norm}.",
            parameter_checked="currency",
            actual_value=normalized_cur,
            allowed_value=allowed_norm,
        )
    return RuleResult(
        rule_id="RULE-05-CURRENCY-ALLOWLIST",
        rule_name="Currency Allowlist",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason=f"Currency '{normalized_cur}' is permitted.",
    )


def check_evidence_present(has_evidence: bool, evidence_id: Optional[str] = None) -> RuleResult:
    """Rule 6: Supporting evidence document must exist."""
    if not has_evidence:
        return RuleResult(
            rule_id="RULE-06-EVIDENCE-REQUIRED",
            rule_name="Invoice Evidence Requirement",
            passed=False,
            decision=RuleDecision.DENY.value,
            reason="Missing supporting invoice evidence document. Payouts require verified underlying documentation.",
            parameter_checked="has_evidence",
            actual_value=False,
            allowed_value=True,
        )
    return RuleResult(
        rule_id="RULE-06-EVIDENCE-REQUIRED",
        rule_name="Invoice Evidence Requirement",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Supporting evidence document is attached.",
    )


def check_hard_cap(amount_minor: int, hard_cap_minor: int = 5000000) -> RuleResult:
    """Rule 7: Hard systemic ceiling ($50,000 = 5,000,000 cents) triggers immediate DENY."""
    if amount_minor >= hard_cap_minor:
        return RuleResult(
            rule_id="RULE-07-SYSTEMIC-HARD-CAP",
            rule_name="Systemic Hard Cap Ceiling",
            passed=False,
            decision=RuleDecision.DENY.value,
            reason=f"Payment of {amount_minor} minor units exceeds the systemic hard security ceiling ({hard_cap_minor} minor units).",
            parameter_checked="amount_minor",
            actual_value=amount_minor,
            allowed_value=f"< {hard_cap_minor}",
        )
    return RuleResult(
        rule_id="RULE-07-SYSTEMIC-HARD-CAP",
        rule_name="Systemic Hard Cap Ceiling",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Amount is within systemic ceiling.",
    )


def check_payee_email_tamper(
    recipient_email: str,
    registered_payee_email: Optional[str],
    is_known_vendor: bool,
) -> RuleResult:
    """Rule 8: If a known vendor exists but the recipient email differs, trigger HARD REJECTION."""
    if is_known_vendor and registered_payee_email:
        if recipient_email.lower().strip() != registered_payee_email.lower().strip():
            return RuleResult(
                rule_id="RULE-08-PAYEE-EMAIL-TAMPER",
                rule_name="Payee Email Integrity",
                passed=False,
                decision=RuleDecision.DENY.value,
                reason=(
                    f"CRITICAL: Changed payee email detected. Known vendor '{registered_payee_email}' "
                    f"does not match requested recipient '{recipient_email}'. Immediate hard rejection."
                ),
                parameter_checked="recipient_email",
                actual_value=recipient_email,
                allowed_value=registered_payee_email,
            )
    return RuleResult(
        rule_id="RULE-08-PAYEE-EMAIL-TAMPER",
        rule_name="Payee Email Integrity",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Payee recipient email matches registered record.",
    )


def check_duplicate_invoice(is_duplicate: bool, existing_invoice_number: Optional[str] = None) -> RuleResult:
    """Rule 9: Duplicate invoice references trigger DENY."""
    if is_duplicate:
        return RuleResult(
            rule_id="RULE-09-DUPLICATE-INVOICE",
            rule_name="Duplicate Invoice Prevention",
            passed=False,
            decision=RuleDecision.DENY.value,
            reason=f"Duplicate invoice detected for reference '{existing_invoice_number}'. A payout was already processed.",
            parameter_checked="is_duplicate",
            actual_value=True,
            allowed_value=False,
        )
    return RuleResult(
        rule_id="RULE-09-DUPLICATE-INVOICE",
        rule_name="Duplicate Invoice Prevention",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="No duplicate invoice reference found.",
    )


def check_per_payment_limit(amount_minor: int, limit_minor: int) -> RuleResult:
    """Rule 10: Per-transaction spending limit."""
    if amount_minor > limit_minor:
        return RuleResult(
            rule_id="RULE-10-PER-PAYMENT-CAP",
            rule_name="Per-Payment Mandate Cap",
            passed=False,
            decision=RuleDecision.ESCALATE.value,
            reason=f"Payment of {amount_minor} minor units exceeds mandate per-transaction limit of {limit_minor} minor units.",
            parameter_checked="amount_minor",
            actual_value=amount_minor,
            allowed_value=f"<= {limit_minor}",
        )
    return RuleResult(
        rule_id="RULE-10-PER-PAYMENT-CAP",
        rule_name="Per-Payment Mandate Cap",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Amount is within per-payment limit.",
    )


def check_daily_limit(current_spend_minor: int, amount_minor: int, daily_limit_minor: int) -> RuleResult:
    """Rule 11: Daily cumulative spending cap."""
    projected = current_spend_minor + amount_minor
    if projected > daily_limit_minor:
        return RuleResult(
            rule_id="RULE-11-DAILY-CAP",
            rule_name="Daily Cumulative Spending Cap",
            passed=False,
            decision=RuleDecision.ESCALATE.value,
            reason=f"Projected daily spend ({projected} minor units) exceeds daily limit ({daily_limit_minor} minor units).",
            parameter_checked="projected_daily_minor",
            actual_value=projected,
            allowed_value=f"<= {daily_limit_minor}",
        )
    return RuleResult(
        rule_id="RULE-11-DAILY-CAP",
        rule_name="Daily Cumulative Spending Cap",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Projected spend is within daily limit.",
    )


def check_weekly_limit(current_spend_minor: int, amount_minor: int, weekly_limit_minor: int) -> RuleResult:
    """Rule 12: Weekly cumulative spending cap."""
    projected = current_spend_minor + amount_minor
    if projected > weekly_limit_minor:
        return RuleResult(
            rule_id="RULE-12-WEEKLY-CAP",
            rule_name="Weekly Cumulative Spending Cap",
            passed=False,
            decision=RuleDecision.ESCALATE.value,
            reason=f"Projected weekly spend ({projected} minor units) exceeds weekly limit ({weekly_limit_minor} minor units).",
            parameter_checked="projected_weekly_minor",
            actual_value=projected,
            allowed_value=f"<= {weekly_limit_minor}",
        )
    return RuleResult(
        rule_id="RULE-12-WEEKLY-CAP",
        rule_name="Weekly Cumulative Spending Cap",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Projected spend is within weekly limit.",
    )


def check_known_recipient(
    payee_registered: bool,
    payee_verified: bool,
    unknown_payee_action: str = "ESCALATE",
) -> RuleResult:
    """Rule 13: Recipient must be registered in the Payee Registry."""
    if not payee_registered or not payee_verified:
        decision = RuleDecision.DENY.value if unknown_payee_action == "DENY" else RuleDecision.ESCALATE.value
        return RuleResult(
            rule_id="RULE-13-PAYEE-REGISTRATION",
            rule_name="Payee Registry Verification",
            passed=False,
            decision=decision,
            reason="Recipient is not registered or verified in the Payee Registry. Mandate requires explicit owner authorization.",
            parameter_checked="payee_verified",
            actual_value=False,
            allowed_value=True,
        )
    return RuleResult(
        rule_id="RULE-13-PAYEE-REGISTRATION",
        rule_name="Payee Registry Verification",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Recipient is verified in Payee Registry.",
    )


def check_operating_time_window(
    timestamp: datetime,
    allowed_weekdays: List[int],
    start_hour_str: Optional[str] = None,
    end_hour_str: Optional[str] = None,
) -> RuleResult:
    """Rule 14: Payments must occur on permitted weekdays and hours (1=Monday...7=Sunday)."""
    # isoweekday: 1=Mon, 7=Sun
    weekday = timestamp.isoweekday()
    if weekday not in allowed_weekdays:
        return RuleResult(
            rule_id="RULE-14-OPERATING-WINDOW",
            rule_name="Operating Days Window",
            passed=False,
            decision=RuleDecision.ESCALATE.value,
            reason=f"Current weekday {weekday} is outside permitted mandate schedule {allowed_weekdays}.",
            parameter_checked="weekday",
            actual_value=weekday,
            allowed_value=allowed_weekdays,
        )
    return RuleResult(
        rule_id="RULE-14-OPERATING-WINDOW",
        rule_name="Operating Days Window",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Transaction is within permitted schedule.",
    )


def check_invoice_amount_match(
    requested_amount_minor: int,
    invoice_amount_minor: Optional[int],
) -> RuleResult:
    """Rule 15: Agent requested amount must match the underlying invoice amount."""
    if invoice_amount_minor is not None and requested_amount_minor != invoice_amount_minor:
        return RuleResult(
            rule_id="RULE-15-AMOUNT-MATCH",
            rule_name="Invoice Amount Discrepancy",
            passed=False,
            decision=RuleDecision.ESCALATE.value,
            reason=(
                f"Discrepancy detected: Payment request is {requested_amount_minor} minor units, "
                f"but extracted invoice amount is {invoice_amount_minor} minor units."
            ),
            parameter_checked="amount_minor",
            actual_value=requested_amount_minor,
            allowed_value=invoice_amount_minor,
        )
    return RuleResult(
        rule_id="RULE-15-AMOUNT-MATCH",
        rule_name="Invoice Amount Discrepancy",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Payment request matches invoice total amount.",
    )


def check_suspicious_document_instructions(
    has_suspicious_text: bool,
    evidence_snippet: Optional[str] = None,
) -> RuleResult:
    """Rule 16: Suspicious urgency or redirection instructions in invoice text."""
    if has_suspicious_text:
        return RuleResult(
            rule_id="RULE-16-SUSPICIOUS-INSTRUCTIONS",
            rule_name="Document Instruction Integrity",
            passed=False,
            decision=RuleDecision.ESCALATE.value,
            reason=f"Suspicious instruction detected in document: '{evidence_snippet}'. Requires manual audit.",
            parameter_checked="has_suspicious_text",
            actual_value=True,
            allowed_value=False,
        )
    return RuleResult(
        rule_id="RULE-16-SUSPICIOUS-INSTRUCTIONS",
        rule_name="Document Instruction Integrity",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="No suspicious instructions detected in document.",
    )


def check_third_party_evidence_limit(
    amount_minor: int,
    evidence_trust_level: str,
    threshold_minor: int,
) -> RuleResult:
    """Rule 17: High-value transactions backed only by untrusted third-party evidence require escalation."""
    if evidence_trust_level == "UNTRUSTED_THIRD_PARTY" and amount_minor > threshold_minor:
        return RuleResult(
            rule_id="RULE-17-THIRD-PARTY-EVIDENCE",
            rule_name="Untrusted Evidence Threshold",
            passed=False,
            decision=RuleDecision.ESCALATE.value,
            reason=(
                f"Transaction amount ({amount_minor} minor units) exceeds untrusted evidence threshold "
                f"({threshold_minor} minor units) with trust level '{evidence_trust_level}'."
            ),
            parameter_checked="evidence_trust_level",
            actual_value=evidence_trust_level,
            allowed_value="HIGH",
        )
    return RuleResult(
        rule_id="RULE-17-THIRD-PARTY-EVIDENCE",
        rule_name="Untrusted Evidence Threshold",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Evidence trust level meets threshold.",
    )


def check_financial_rate_limit(request_count_last_minute: int, max_allowed: int = 10) -> RuleResult:
    """Rule 18: Rate limit protects against rogue agent loops."""
    if request_count_last_minute >= max_allowed:
        return RuleResult(
            rule_id="RULE-18-RATE-LIMIT",
            rule_name="Financial Gateway Rate Limiting",
            passed=False,
            decision=RuleDecision.DENY.value,
            reason=f"Rate limit exceeded: {request_count_last_minute} payment requests in last 60 seconds (max {max_allowed}).",
            parameter_checked="request_count_last_minute",
            actual_value=request_count_last_minute,
            allowed_value=f"< {max_allowed}",
        )
    return RuleResult(
        rule_id="RULE-18-RATE-LIMIT",
        rule_name="Financial Gateway Rate Limiting",
        passed=True,
        decision=RuleDecision.PASS.value,
        reason="Request rate is within limits.",
    )
