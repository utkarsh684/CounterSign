"""Deterministic AI Provider for reproducible testing and offline demonstrations.

Parses natural language prompts and invoice text using deterministic regex & NLP heuristics
matching exactly the same structured schema as live LLM providers.
"""

import re
from typing import Any, Dict, List, Optional
from app.ai.provider import AIProvider
from app.policy.money import dollars_to_minor_units


class FallbackAIProvider(AIProvider):
    async def generate_structured_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        prompt_lower = user_prompt.lower()
        sys_lower = system_prompt.lower()

        # 1. Mandate Compilation
        if "mandate" in sys_lower or "spending" in sys_lower or "financial policy" in sys_lower:
            per_tx = 20000
            weekly = 100000
            daily = 50000

            # Regex search for dollar figures
            # e.g., "$200 per transaction" or "up to $200"
            per_tx_match = re.search(r"\$(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:per\s+transaction|per\s+payment|limit)", prompt_lower)
            if per_tx_match:
                per_tx = dollars_to_minor_units(per_tx_match.group(1).replace(",", ""))

            weekly_match = re.search(r"\$(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:a\s+week|per\s+week|weekly)", prompt_lower)
            if weekly_match:
                weekly = dollars_to_minor_units(weekly_match.group(1).replace(",", ""))

            currencies = ["USD"]
            if "eur" in prompt_lower:
                currencies.append("EUR")

            weekdays = [1, 2, 3, 4, 5]
            if "weekdays only" in prompt_lower or "on weekdays" in prompt_lower:
                weekdays = [1, 2, 3, 4, 5]
            elif "every day" in prompt_lower or "all week" in prompt_lower:
                weekdays = [1, 2, 3, 4, 5, 6, 7]

            allow_existing_only = "only existing" in prompt_lower or "known contractors" in prompt_lower or "existing contractors" in prompt_lower

            return {
                "spec": {
                    "currency_allowlist": currencies,
                    "per_transaction_limit_minor": per_tx,
                    "daily_limit_minor": min(daily, weekly),
                    "weekly_limit_minor": weekly,
                    "allowed_weekdays": weekdays,
                    "operating_hours_start": "09:00",
                    "operating_hours_end": "18:00",
                    "allow_existing_payees_only": allow_existing_only,
                    "unknown_payee_action": "ESCALATE",
                    "third_party_evidence_limit_minor": 10000,
                    "human_confirmation_required": True,
                },
                "explanation": (
                    f"Compiled financial spending mandate permitting payments up to ${per_tx/100:.2f} per transaction "
                    f"and ${weekly/100:.2f} per week in {', '.join(currencies)} during business hours. "
                    f"Unknown recipients will be escalated for owner review."
                ),
                "rules_breakdown": [
                    {
                        "rule": "Per Transaction Cap",
                        "parameter": "per_transaction_limit_minor",
                        "value": f"${per_tx/100:.2f}",
                        "rationale": "Extracted from explicit single-payment spending limit instructions.",
                    },
                    {
                        "rule": "Weekly Cumulative Cap",
                        "parameter": "weekly_limit_minor",
                        "value": f"${weekly/100:.2f}",
                        "rationale": "Enforces global seven-day velocity ceiling.",
                    },
                    {
                        "rule": "Currency Allowlist",
                        "parameter": "currency_allowlist",
                        "value": str(currencies),
                        "rationale": "Restricts payouts exclusively to declared operational currencies.",
                    },
                    {
                        "rule": "Payee Governance",
                        "parameter": "allow_existing_payees_only",
                        "value": str(allow_existing_only),
                        "rationale": "Mandates human verification prior to paying first-time or unrecognized payees.",
                    },
                ],
                "missing_or_ambiguous_conditions": (
                    [] if ("week" in prompt_lower and "transaction" in prompt_lower)
                    else ["Daily spending limit was defaulted based on weekly cap."]
                ),
                "confidence_score": 0.98,
            }

        # 2. Independent AI Security Intent Verifier
        if "security verifier" in system_prompt.lower() or "injection" in system_prompt.lower():
            # Check for known prompt injection / redirection patterns
            suspicious_cues = [
                "ignore previous",
                "banking details have changed",
                "send to billing@",
                "our banking information has changed",
                "system notice",
                "mark this payment approved",
                "approved by the owner",
                "verbal approval",
            ]
            has_injection = any(cue in prompt_lower for cue in suspicious_cues)

            if has_injection:
                return {
                    "risk_level": "HIGH",
                    "recommendation": "DENY",
                    "injection_detected": True,
                    "reason_codes": [
                        "PROMPT_INJECTION_DETECTED",
                        "UNAUTHORIZED_DESTINATION_OVERRIDE",
                        "FALSE_AUTHORITY_CLAIM",
                    ],
                    "evidence_references": ["INVOICE_INSTRUCTION_OVERRIDE"],
                    "explanation": (
                        "CRITICAL SECURITY THREAT: Document contains adversarial instructions attempting to "
                        "override authorized financial controls, alter payment destination email, and falsely "
                        "assert owner pre-authorization. Recommended immediate rejection."
                    ),
                }

            # Check for amount over limit or unusual request
            if "340" in prompt_lower:
                return {
                    "risk_level": "MEDIUM",
                    "recommendation": "ESCALATE",
                    "injection_detected": False,
                    "reason_codes": ["POLICY_SOFT_CAP_EXCEEDED"],
                    "evidence_references": ["INV-2210"],
                    "explanation": (
                        "Legitimate vendor invoice from Dev Studio, but total amount ($340.00) exceeds "
                        "the standard per-transaction mandate allowance ($200.00). Escalated for owner authorization."
                    ),
                }

            # Default clean verification
            return {
                "risk_level": "LOW",
                "recommendation": "CLEAR",
                "injection_detected": False,
                "reason_codes": ["VERIFIED_KNOWN_CONTRACTOR", "AMOUNT_WITHIN_LIMITS"],
                "evidence_references": ["INV-1042"],
                "explanation": (
                    "Proposed transaction aligns with active spending mandate and verified contractor invoice. "
                    "No anomalous instructions or destination discrepancies detected."
                ),
            }

        return {}
