import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import FlashcardDeckModel, DocumentModel
from app.schemas.schemas import (
    FlashcardDeckGenerateRequest,
    FlashcardDeckResponse,
    Flashcard
)
from app.agents.flashcard_agent import FlashcardAgent

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])


@router.post("/generate", response_model=FlashcardDeckResponse, status_code=status.HTTP_201_CREATED)
def generate_flashcards(
    payload: FlashcardDeckGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Invokes FlashcardAgent to generate spaced-repetition flashcards.
    """
    doc = db.query(DocumentModel).filter(DocumentModel.id == payload.document_id).first()
    doc_name = doc.filename if doc else "Course Materials"
    topic = payload.topic or (doc.subject if doc else "Core Concepts")

    deck_record = FlashcardAgent.generate_deck(
        document_id=payload.document_id,
        document_name=doc_name,
        topic=topic,
        card_count=payload.card_count,
        db=db
    )

    cards = [Flashcard(**c) for c in json.loads(deck_record.cards_json)]
    return FlashcardDeckResponse(
        id=deck_record.id,
        document_id=deck_record.document_id,
        title=deck_record.title,
        topic=deck_record.topic,
        card_count=len(cards),
        cards=cards,
        created_at=deck_record.created_at
    )


@router.get("/list", response_model=List[FlashcardDeckResponse])
def list_decks(db: Session = Depends(get_db)):
    """List all created flashcard decks."""
    decks = db.query(FlashcardDeckModel).order_by(FlashcardDeckModel.created_at.desc()).all()
    results = []
    for d in decks:
        cards = [Flashcard(**c) for c in json.loads(d.cards_json)]
        results.append(FlashcardDeckResponse(
            id=d.id,
            document_id=d.document_id,
            title=d.title,
            topic=d.topic,
            card_count=len(cards),
            cards=cards,
            created_at=d.created_at
        ))
    return results
