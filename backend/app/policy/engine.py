"""Deterministic Payment Policy Engine.

Evaluates payment requests against the active financial mandate, payee registry,
and systemic safety controls.
Guarantees:
- Pure deterministic execution (zero LLM reliance for hard limits).
- If ANY rule results in DENY -> Outcome is DENY.
- If any rule results in ESCALATE and none DENY -> Outcome is ESCALATE.
- If all rules pass -> Outcome is READY_FOR_APPROVAL.
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.policy.decision import PolicyOutcome, RuleDecision
from app.policy.rules import (
    check_kill_switch,
    check_mandate_active,
    check_mandate_not_revoked,
    check_valid_amount,
    check_currency_allowlist,
    check_evidence_present,
    check_hard_cap,
    check_payee_email_tamper,
    check_duplicate_invoice,
    check_per_payment_limit,
    check_daily_limit,
    check_weekly_limit,
    check_known_recipient,
    check_operating_time_window,
    check_invoice_amount_match,
    check_suspicious_document_instructions,
    check_third_party_evidence_limit,
    check_financial_rate_limit,
)
from app.schemas.payment import PolicyEvaluationResponse, RuleResult


class PolicyContext:
    def __init__(
        self,
        amount_minor: int,
        currency: str,
        recipient_email: str,
        mandate_status: str = "ACTIVE",
        is_mandate_revoked: bool = False,
        currency_allowlist: Optional[List[str]] = None,
        per_transaction_limit_minor: int = 20000,
        daily_limit_minor: int = 50000,
        weekly_limit_minor: int = 100000,
        allowed_weekdays: Optional[List[int]] = None,
        current_daily_spend_minor: int = 0,
        current_weekly_spend_minor: int = 0,
        payee_registered: bool = True,
        payee_verified: bool = True,
        registered_payee_email: Optional[str] = None,
        is_known_vendor: bool = True,
        unknown_payee_action: str = "ESCALATE",
        has_evidence: bool = True,
        evidence_trust_level: str = "HIGH",
        third_party_evidence_limit_minor: int = 10000,
        is_duplicate_invoice: bool = False,
        existing_invoice_number: Optional[str] = None,
        invoice_amount_minor: Optional[int] = None,
        has_suspicious_text: bool = False,
        suspicious_snippet: Optional[str] = None,
        request_count_last_minute: int = 1,
        timestamp: Optional[datetime] = None,
        kill_switch_enabled: Optional[bool] = None,
    ):
        self.amount_minor = amount_minor
        self.currency = currency
        self.recipient_email = recipient_email
        self.mandate_status = mandate_status
        self.is_mandate_revoked = is_mandate_revoked
        self.currency_allowlist = currency_allowlist or ["USD"]
        self.per_transaction_limit_minor = per_transaction_limit_minor
        self.daily_limit_minor = daily_limit_minor
        self.weekly_limit_minor = weekly_limit_minor
        self.allowed_weekdays = allowed_weekdays or [1, 2, 3, 4, 5]
        self.current_daily_spend_minor = current_daily_spend_minor
        self.current_weekly_spend_minor = current_weekly_spend_minor
        self.payee_registered = payee_registered
        self.payee_verified = payee_verified
        self.registered_payee_email = registered_payee_email or recipient_email
        self.is_known_vendor = is_known_vendor
        self.unknown_payee_action = unknown_payee_action
        self.has_evidence = has_evidence
        self.evidence_trust_level = evidence_trust_level
        self.third_party_evidence_limit_minor = third_party_evidence_limit_minor
        self.is_duplicate_invoice = is_duplicate_invoice
        self.existing_invoice_number = existing_invoice_number
        self.invoice_amount_minor = invoice_amount_minor
        self.has_suspicious_text = has_suspicious_text
        self.suspicious_snippet = suspicious_snippet
        self.request_count_last_minute = request_count_last_minute
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.kill_switch_enabled = (
            kill_switch_enabled if kill_switch_enabled is not None else settings.KILL_SWITCH_ENABLED
        )


class DeterministicPolicyEngine:
    @staticmethod
    def evaluate(ctx: PolicyContext) -> PolicyEvaluationResponse:
        start_time = time.perf_counter()
        results: List[RuleResult] = []

        # 1. Kill switch
        results.append(check_kill_switch(ctx.kill_switch_enabled))

        # 2. Mandate status
        results.append(check_mandate_active(ctx.mandate_status))

        # 3. Mandate revocation
        results.append(check_mandate_not_revoked(ctx.is_mandate_revoked))

        # 4. Valid amount
        results.append(check_valid_amount(ctx.amount_minor))

        # 5. Currency allowlist
        results.append(check_currency_allowlist(ctx.currency, ctx.currency_allowlist))

        # 6. Evidence required
        results.append(check_evidence_present(ctx.has_evidence))

        # 7. Systemic hard cap ($50,000 ceiling)
        results.append(check_hard_cap(ctx.amount_minor))

        # 8. Payee email tampering (hard rejection)
        results.append(
            check_payee_email_tamper(
                recipient_email=ctx.recipient_email,
                registered_payee_email=ctx.registered_payee_email,
                is_known_vendor=ctx.is_known_vendor,
            )
        )

        # 9. Duplicate invoice prevention
        results.append(check_duplicate_invoice(ctx.is_duplicate_invoice, ctx.existing_invoice_number))

        # 10. Per-payment mandate limit
        results.append(check_per_payment_limit(ctx.amount_minor, ctx.per_transaction_limit_minor))

        # 11. Daily cumulative limit
        results.append(check_daily_limit(ctx.current_daily_spend_minor, ctx.amount_minor, ctx.daily_limit_minor))

        # 12. Weekly cumulative limit
        results.append(check_weekly_limit(ctx.current_weekly_spend_minor, ctx.amount_minor, ctx.weekly_limit_minor))

        # 13. Payee registry verification
        results.append(
            check_known_recipient(
                payee_registered=ctx.payee_registered,
                payee_verified=ctx.payee_verified,
                unknown_payee_action=ctx.unknown_payee_action,
            )
        )

        # 14. Operating window / weekdays
        results.append(
            check_operating_time_window(
                timestamp=ctx.timestamp,
                allowed_weekdays=ctx.allowed_weekdays,
            )
        )

        # 15. Invoice vs requested amount match
        results.append(
            check_invoice_amount_match(
                requested_amount_minor=ctx.amount_minor,
                invoice_amount_minor=ctx.invoice_amount_minor,
            )
        )

        # 16. Suspicious instructions in document
        results.append(
            check_suspicious_document_instructions(
                has_suspicious_text=ctx.has_suspicious_text,
                evidence_snippet=ctx.suspicious_snippet,
            )
        )

        # 17. High-value third-party untrusted evidence
        results.append(
            check_third_party_evidence_limit(
                amount_minor=ctx.amount_minor,
                evidence_trust_level=ctx.evidence_trust_level,
                threshold_minor=ctx.third_party_evidence_limit_minor,
            )
        )

        # 18. Financial rate limit
        results.append(check_financial_rate_limit(ctx.request_count_last_minute))

        # Calculate outcomes
        has_deny = any(r.decision == RuleDecision.DENY.value for r in results)
        has_escalate = any(r.decision == RuleDecision.ESCALATE.value for r in results)

        if has_deny:
            outcome = PolicyOutcome.DENY.value
        elif has_escalate:
            outcome = PolicyOutcome.ESCALATE.value
        else:
            outcome = PolicyOutcome.READY_FOR_APPROVAL.value

        passed_count = sum(1 for r in results if r.passed)
        failed_count = sum(1 for r in results if not r.passed)
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return PolicyEvaluationResponse(
            outcome=outcome,
            rules_evaluated=len(results),
            rules_passed=passed_count,
            rules_failed=failed_count,
            rule_results=results,
            latency_ms=latency_ms,
            evaluated_at=datetime.now(timezone.utc),
        )
