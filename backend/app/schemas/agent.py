"""AI Agent and Scenario schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AgentToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Any


class AgentExecutionStep(BaseModel):
    step_number: int
    thought: str
    tool_call: Optional[AgentToolCall] = None
    observation: Optional[str] = None


class AgentProcessResponse(BaseModel):
    agent_id: str
    mode: str  # LIVE or SCRIPTED_COMPROMISED
    invoice_id: str
    steps: List[AgentExecutionStep]
    payment_request_id: Optional[str] = None
    outcome_decision: str
    decision_reason: str


class ScenarioExecutionResult(BaseModel):
    scenario_id: str
    name: str
    scenario_type: str  # ATTACK or BENIGN
    description: str
    simulated_agent_mode: str
    attempted_action: Dict[str, Any]
    policy_outcome: str
    ai_risk_level: str
    ai_injection_detected: bool
    final_decision: str  # BLOCKED, ESCALATED, READY_FOR_APPROVAL
    blocked_reason: Optional[str] = None
    reached_paypal: bool  # MUST ALWAYS BE FALSE FOR ATTACK SCENARIOS
    evaluation_latency_ms: int
