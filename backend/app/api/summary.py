import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import SummaryModel, DocumentModel
from app.schemas.schemas import (
    SummaryGenerateRequest,
    SummaryResponse
)
from app.agents.summary_agent import SummaryAgent

router = APIRouter(prefix="/summary", tags=["Summaries"])


@router.post("/generate", response_model=SummaryResponse, status_code=status.HTTP_201_CREATED)
def generate_summary(
    payload: SummaryGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Invokes SummaryAgent to generate an educational summary in one of 5 modes
    (short, detailed, key_points, beginner, exam_notes).
    """
    doc = db.query(DocumentModel).filter(DocumentModel.id == payload.document_id).first()
    doc_name = doc.filename if doc else "Course Materials"
    topic = payload.topic or (doc.subject if doc else "Chapter Overview")

    summary_record = SummaryAgent.generate_summary(
        document_id=payload.document_id,
        document_name=doc_name,
        topic=topic,
        mode=payload.mode,
        db=db
    )

    key_points = json.loads(summary_record.key_points_json) if summary_record.key_points_json else []
    return SummaryResponse(
        id=summary_record.id,
        document_id=summary_record.document_id,
        title=summary_record.title,
        topic=summary_record.topic,
        mode=summary_record.mode,
        content=summary_record.content,
        key_points=key_points,
        created_at=summary_record.created_at
    )


@router.get("/list", response_model=List[SummaryResponse])
def list_summaries(db: Session = Depends(get_db)):
    """List all generated summaries."""
    summaries = db.query(SummaryModel).order_by(SummaryModel.created_at.desc()).all()
    results = []
    for s in summaries:
        key_points = json.loads(s.key_points_json) if s.key_points_json else []
        results.append(SummaryResponse(
            id=s.id,
            document_id=s.document_id,
            title=s.title,
            topic=s.topic,
            mode=s.mode,
            content=s.content,
            key_points=key_points,
            created_at=s.created_at
        ))
    return results
