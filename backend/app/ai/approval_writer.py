"""Advisory Human-Readable Approval Briefing Writer."""

from app.policy.money import minor_units_to_formatted_string


class ApprovalWriterService:
    @staticmethod
    def generate_advisory_summary(
        vendor_name: str,
        recipient_email: str,
        amount_minor: int,
        currency: str,
        invoice_number: str,
        policy_outcome: str,
        ai_risk_level: str,
        ai_explanation: str,
        is_simulated: bool = False,
    ) -> str:
        formatted_amount = minor_units_to_formatted_string(amount_minor, currency)
        prefix = "[SIMULATED DEMONSTRATION] " if is_simulated else ""

        if policy_outcome == "DENY":
            return (
                f"{prefix}DENIED TRANSACTION: Agent attempted to initiate {formatted_amount} payout "
                f"to '{recipient_email}' for {vendor_name} ({invoice_number}). "
                f"Blocked by deterministic financial policies. Reason: {ai_explanation} "
                f"Advisory notice: This attempt was halted at the gateway and never reached PayPal."
            )
        elif policy_outcome == "ESCALATE":
            return (
                f"{prefix}ACTION REQUIRED: Proposed payment of {formatted_amount} to '{recipient_email}' "
                f"for {vendor_name} ({invoice_number}) requires your explicit authorization. "
                f"Policy evaluation flagged soft limits. Security Verifier Risk: {ai_risk_level}. "
                f"{ai_explanation}"
            )
        else:
            return (
                f"{prefix}CLEARED FOR AUTHORIZATION: Payment of {formatted_amount} to verified contractor "
                f"'{recipient_email}' ({invoice_number}) has passed all 18 deterministic rules and "
                f"independent AI intent verification. Awaiting your explicit final sign-off."
            )
