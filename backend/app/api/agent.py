import json
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import AgentLogModel
from app.schemas.schemas import (
    ChatMessageRequest,
    ChatMessageResponse,
    AgentLogResponse
)
from app.agents.coordinator_agent import CoordinatorAgent

router = APIRouter(prefix="/agent", tags=["Agent Orchestrator"])


@router.post("/chat", response_model=ChatMessageResponse)
def student_chat(
    payload: ChatMessageRequest,
    db: Session = Depends(get_db)
):
    """
    Primary Agentic Chat Endpoint.
    CoordinatorAgent evaluates intent, executes RAG retrieval or specialized educational agents,
    and returns a grounded answer with page citations.
    """
    return CoordinatorAgent.handle_student_interaction(
        message=payload.message,
        document_id=payload.document_id,
        pedagogical_mode=payload.pedagogical_mode,
        db=db
    )


@router.get("/logs", response_model=List[AgentLogResponse])
def get_agent_logs(limit: int = 25, db: Session = Depends(get_db)):
    """
    Returns audit trail of autonomous agent decisions, tool invocations, and execution latency.
    """
    logs = db.query(AgentLogModel).order_by(AgentLogModel.timestamp.desc()).limit(limit).all()
    results = []
    for lg in logs:
        try:
            tools = json.loads(lg.tools_invoked) if lg.tools_invoked else []
        except Exception:
            tools = []
        results.append(AgentLogResponse(
            id=lg.id,
            timestamp=lg.timestamp,
            agent_name=lg.agent_name,
            user_query=lg.user_query,
            detected_intent=lg.detected_intent,
            decision_rationale=lg.decision_rationale,
            tools_invoked=tools,
            execution_time_ms=lg.execution_time_ms,
            status=lg.status,
            output_summary=lg.output_summary
        ))
    return results
