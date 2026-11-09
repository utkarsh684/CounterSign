"""AI Spending Mandate Compiler Service.

Transforms natural language instructions into typed, schema-validated financial constraints.
Enforces:
- Structured Pydantic validation (never trusts raw LLM text).
- Integer minor units.
- Explanations for every extracted rule.
- Ambiguity highlighting.
- Never silently invents missing limits.
"""

from typing import Any, Dict
from app.ai.gemini_provider import GeminiAIProvider
from app.ai.fallback_provider import FallbackAIProvider
from app.core.config import settings
from app.schemas.mandate import (
    MandateCompileRequest,
    MandateCompileResponse,
    MandateSpec,
    RuleExplanation,
)

SYSTEM_PROMPT = """You are Countersign's Principal Financial Policy Architect.
Your task is to compile plain-English business spending instructions into an immutable, structured financial policy.

CRITICAL INSTRUCTIONS:
1. All monetary caps must be represented strictly as integer minor units (e.g. cents). $200 = 20000.
2. Allowed weekdays must be an array of integers (1=Monday ... 7=Sunday).
3. Currency must be an ISO 4217 code list, defaulting to ["USD"].
4. You must explain every extracted rule.
5. You must never silently invent or assume financial authority. Highlight any ambiguous conditions.
6. Return strictly valid JSON adhering to the target schema.
"""


class MandateCompilerService:
    @classmethod
    def _get_provider(cls):
        if settings.AI_PROVIDER == "gemini":
            return GeminiAIProvider()
        return FallbackAIProvider()

    @classmethod
    async def compile_mandate(cls, request: MandateCompileRequest) -> MandateCompileResponse:
        provider = cls._get_provider()
        user_prompt = f"Spending Instructions: \"{request.prompt}\"\nMandate Title: \"{request.title}\""

        raw_result = await provider.generate_structured_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        spec_data = raw_result.get("spec", {})
        spec = MandateSpec(
            currency_allowlist=spec_data.get("currency_allowlist", ["USD"]),
            per_transaction_limit_minor=spec_data.get("per_transaction_limit_minor", 20000),
            daily_limit_minor=spec_data.get("daily_limit_minor", 50000),
            weekly_limit_minor=spec_data.get("weekly_limit_minor", 100000),
            allowed_weekdays=spec_data.get("allowed_weekdays", [1, 2, 3, 4, 5]),
            operating_hours_start=spec_data.get("operating_hours_start", "09:00"),
            operating_hours_end=spec_data.get("operating_hours_end", "18:00"),
            allow_existing_payees_only=spec_data.get("allow_existing_payees_only", True),
            unknown_payee_action=spec_data.get("unknown_payee_action", "ESCALATE"),
            third_party_evidence_limit_minor=spec_data.get("third_party_evidence_limit_minor", 10000),
            human_confirmation_required=True,
        )

        rules_data = raw_result.get("rules_breakdown", [])
        rules_breakdown = [RuleExplanation(**r) for r in rules_data]

        return MandateCompileResponse(
            spec=spec,
            explanation=raw_result.get("explanation", "Compiled financial spending mandate."),
            rules_breakdown=rules_breakdown,
            missing_or_ambiguous_conditions=raw_result.get("missing_or_ambiguous_conditions", []),
            confidence_score=raw_result.get("confidence_score", 0.95),
        )
