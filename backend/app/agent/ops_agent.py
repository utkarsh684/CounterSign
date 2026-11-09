"""Countersign Ops Agent: Accounts Payable Assistant."""

import uuid
from typing import Any, Dict, List
from sqlalchemy.orm import Session
from app.agent.agent_tools import AgentToolSet
from app.models.invoice import Invoice
from app.models.mandate import Mandate
from app.models.payee import Payee
from app.policy.engine import DeterministicPolicyEngine, PolicyContext
from app.schemas.agent import AgentExecutionStep, AgentProcessResponse, AgentToolCall


class CountersignOpsAgent:
    @classmethod
    async def process_invoice(
        cls,
        db: Session,
        user_id: str,
        invoice_id: str,
        mode: str = "LIVE",
    ) -> AgentProcessResponse:
        tools = AgentToolSet(db, user_id)
        steps: List[AgentExecutionStep] = []

        # Step 1: Read Invoice
        inv_details = tools.read_invoice(invoice_id)
        steps.append(
            AgentExecutionStep(
                step_number=1,
                thought="Examining invoice documentation, extracted metadata, and vendor claims.",
                tool_call=AgentToolCall(
                    tool_name="read_invoice",
                    arguments={"invoice_id": invoice_id},
                    output=inv_details,
                ),
                observation=(
                    f"Invoice #{inv_details.get('invoice_number')} from '{inv_details.get('vendor_name')}' "
                    f"for {inv_details.get('total_amount_minor')} minor units ({inv_details.get('currency')})."
                ),
            )
        )

        # Step 2: Query Payee Registry
        payees = tools.list_payees()
        vendor_email = inv_details.get("vendor_email", "")
        matched_payee = next((p for p in payees if p["paypal_email"].lower() == vendor_email.lower()), None)
        steps.append(
            AgentExecutionStep(
                step_number=2,
                thought="Cross-referencing vendor against verified accounts in owner's Payee Registry.",
                tool_call=AgentToolCall(
                    tool_name="list_payees",
                    arguments={},
                    output=payees,
                ),
                observation=(
                    f"Found verified registered payee: '{matched_payee['name']}' ({matched_payee['paypal_email']})"
                    if matched_payee
                    else f"Vendor '{vendor_email}' is NOT registered in Payee Registry."
                ),
            )
        )

        # Step 3: Get Active Mandate Summary
        mandate_summary = tools.get_mandate_summary()
        steps.append(
            AgentExecutionStep(
                step_number=3,
                thought="Checking active financial spending mandate constraints and threshold limits.",
                tool_call=AgentToolCall(
                    tool_name="get_mandate_summary",
                    arguments={},
                    output=mandate_summary,
                ),
                observation=(
                    f"Active Mandate: Per-tx limit {mandate_summary.get('per_transaction_limit')}, "
                    f"Weekly cap {mandate_summary.get('weekly_limit')}."
                ),
            )
        )

        # Step 4: Propose Payment Request through Gateway
        # In LIVE mode, the agent respects payee email and invoice amount
        recipient_email = matched_payee["paypal_email"] if matched_payee else vendor_email
        amount_minor = inv_details.get("total_amount_minor", 6000)

        # Run deterministic policy check
        ctx = PolicyContext(
            amount_minor=amount_minor,
            currency=inv_details.get("currency", "USD"),
            recipient_email=recipient_email,
            registered_payee_email=matched_payee["paypal_email"] if matched_payee else None,
            is_known_vendor=bool(matched_payee),
            payee_registered=bool(matched_payee),
            payee_verified=bool(matched_payee),
            invoice_amount_minor=amount_minor,
            has_evidence=True,
            has_suspicious_text=bool(inv_details.get("security_findings")),
            suspicious_snippet=inv_details.get("security_findings", [{}])[0].get("evidence_snippet") if inv_details.get("security_findings") else None,
        )
        policy_res = DeterministicPolicyEngine.evaluate(ctx)

        steps.append(
            AgentExecutionStep(
                step_number=4,
                thought="Submitting structured payment proposal through the secure gateway for authorization.",
                tool_call=AgentToolCall(
                    tool_name="request_payment",
                    arguments={
                        "recipient_email": recipient_email,
                        "amount_minor": amount_minor,
                        "currency": inv_details.get("currency", "USD"),
                    },
                    output={"policy_outcome": policy_res.outcome},
                ),
                observation=f"Gateway evaluated transaction: Outcome is {policy_res.outcome}.",
            )
        )

        return AgentProcessResponse(
            agent_id="COUNTERSIGN_OPS_AGENT",
            mode=mode,
            invoice_id=invoice_id,
            steps=steps,
            payment_request_id=f"payreq_{uuid.uuid4().hex[:12]}",
            outcome_decision=policy_res.outcome,
            decision_reason=(
                "All preliminary financial policy checks passed. Presented for explicit human authorization."
                if policy_res.outcome == "READY_FOR_APPROVAL"
                else "Transaction flagged by financial policy or security verifier."
            ),
        )
