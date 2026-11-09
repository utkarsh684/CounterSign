"""AI Operations Agent and Injection Lab Execution Routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.agent.ops_agent import CountersignOpsAgent
from app.core.dependencies import get_current_owner, get_db
from app.models.user import User
from app.redteam.scenarios import SCENARIOS, run_all_scenarios, run_scenario
from app.schemas.agent import AgentProcessResponse, ScenarioExecutionResult

router = APIRouter(prefix="/agent", tags=["AI Operations Agent & Red-Team"])


class AgentProcessRequest(BaseModel):
    invoice_id: str
    mode: str = "LIVE"  # LIVE or SCRIPTED_COMPROMISED


class ScenarioRunRequest(BaseModel):
    scenario_id: str


@router.post("/process", response_model=AgentProcessResponse)
async def process_invoice_with_agent(
    data: AgentProcessRequest,
    owner: User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Executes the Countersign Ops Agent to parse, cross-reference, and propose payment."""
    return await CountersignOpsAgent.process_invoice(
        db=db,
        user_id=owner.id,
        invoice_id=data.invoice_id,
        mode=data.mode,
    )


@router.get("/scenarios", response_model=List[ScenarioExecutionResult])
def list_and_execute_all_scenarios():
    """Runs all 18 attack and benign test scenarios and returns live scoreboard metrics."""
    return run_all_scenarios()


@router.post("/run-scenario", response_model=ScenarioExecutionResult)
def execute_single_scenario(data: ScenarioRunRequest):
    """Runs an individual red-team or benign scenario."""
    return run_scenario(data.scenario_id)


@router.get("/status")
def get_agent_status():
    return {
        "agent_name": "Countersign Ops Agent",
        "role": "Accounts Payable Assistant",
        "has_payout_execution_tool": False,  # Strict boundary
        "allowed_tools": [
            "read_inbox",
            "read_invoice",
            "list_payees",
            "get_mandate_summary",
            "request_payment",
        ],
        "modes_supported": ["LIVE", "SCRIPTED_COMPROMISED"],
    }
