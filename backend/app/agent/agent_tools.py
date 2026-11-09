"""Authorized tool boundaries for the Countersign Ops Agent.

CRITICAL SECURITY REQUIREMENT:
The agent MUST NEVER possess:
- execute_payment() tool
- PayPal credentials
- Mandate override tools
- Direct database write tools
Allowed tools are strictly read-only plus request_payment() gateway submission.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.invoice import Invoice
from app.models.mandate import Mandate, MandateVersion
from app.models.payee import Payee
from app.policy.money import minor_units_to_formatted_string


class AgentToolSet:
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def read_inbox(self) -> List[Dict[str, Any]]:
        """Tool 1: Read pending invoices awaiting payment processing."""
        invoices = self.db.query(Invoice).filter(
            Invoice.user_id == self.user_id,
            Invoice.status.in_(["PENDING", "ANALYZED"]),
        ).all()
        return [
            {
                "invoice_id": inv.id,
                "invoice_number": inv.invoice_number,
                "vendor_name": inv.vendor_name,
                "vendor_email": inv.vendor_email,
                "amount": minor_units_to_formatted_string(inv.total_amount_minor, inv.currency),
                "currency": inv.currency,
                "status": inv.status,
            }
            for inv in invoices
        ]

    def read_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Tool 2: Inspect raw invoice text and extracted metadata."""
        inv = self.db.query(Invoice).filter(
            Invoice.id == invoice_id,
            Invoice.user_id == self.user_id,
        ).first()
        if not inv:
            return {"error": f"Invoice {invoice_id} not found"}
        return {
            "invoice_id": inv.id,
            "invoice_number": inv.invoice_number,
            "vendor_name": inv.vendor_name,
            "vendor_email": inv.vendor_email,
            "currency": inv.currency,
            "total_amount_minor": inv.total_amount_minor,
            "raw_text": inv.raw_text or "",
            "payment_instructions": inv.payment_instructions or "",
            "security_findings": inv.security_findings,
        }

    def list_payees(self) -> List[Dict[str, Any]]:
        """Tool 3: Consult the owner-controlled Payee Registry."""
        payees = self.db.query(Payee).filter(
            Payee.user_id == self.user_id,
            Payee.verification_status == "VERIFIED",
        ).all()
        return [
            {
                "payee_id": p.id,
                "name": p.name,
                "paypal_email": p.paypal_email,
                "category": p.category,
                "trust_status": p.trust_status,
                "total_paid": minor_units_to_formatted_string(p.total_paid_minor),
            }
            for p in payees
        ]

    def get_mandate_summary(self) -> Dict[str, Any]:
        """Tool 4: Understand the active spending mandate limits."""
        mandate = self.db.query(Mandate).filter(
            Mandate.user_id == self.user_id,
            Mandate.status == "ACTIVE",
        ).first()
        if not mandate or not mandate.versions:
            return {"status": "NO_ACTIVE_MANDATE"}

        active_v = mandate.versions[0]
        return {
            "mandate_id": mandate.id,
            "version": active_v.version,
            "per_transaction_limit": minor_units_to_formatted_string(active_v.per_transaction_limit_minor),
            "weekly_limit": minor_units_to_formatted_string(active_v.weekly_limit_minor),
            "allowed_currencies": active_v.currency_allowlist,
            "allow_existing_payees_only": active_v.allow_existing_payees_only,
            "unknown_payee_action": active_v.unknown_payee_action,
        }
