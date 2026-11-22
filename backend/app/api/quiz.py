import json
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import QuizModel, QuizAttemptModel, DocumentModel
from app.schemas.schemas import (
    QuizGenerateRequest,
    QuizResponse,
    QuizSubmitRequest,
    QuizResultResponse,
    QuizQuestion,
    QuestionEvaluation
)
from app.agents.quiz_agent import QuizAgent

router = APIRouter(prefix="/quiz", tags=["Quizzes"])


@router.post("/generate", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
def generate_quiz(
    payload: QuizGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Invokes QuizAgent to generate a calibrated educational assessment
    grounded in uploaded document context.
    """
    doc = db.query(DocumentModel).filter(DocumentModel.id == payload.document_id).first()
    doc_name = doc.filename if doc else "Academic Curriculum"
    topic = payload.topic or (doc.subject if doc else "General Concepts")

    quiz_record = QuizAgent.generate_quiz(
        document_id=payload.document_id,
        document_name=doc_name,
        topic=topic,
        difficulty=payload.difficulty,
        question_count=payload.question_count,
        question_types=payload.question_types,
        db=db
    )

    questions = [QuizQuestion(**q) for q in json.loads(quiz_record.questions_json)]
    return QuizResponse(
        id=quiz_record.id,
        document_id=quiz_record.document_id,
        title=quiz_record.title,
        topic=quiz_record.topic,
        difficulty=quiz_record.difficulty,
        question_count=quiz_record.question_count,
        questions=questions,
        created_at=quiz_record.created_at
    )


@router.post("/submit", response_model=QuizResultResponse)
def submit_quiz_attempt(
    payload: QuizSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates student quiz answers, calculates percentage score,
    persists attempt in SQLite, and updates topic mastery statistics.
    """
    quiz = db.query(QuizModel).filter(QuizModel.id == payload.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    questions_list = json.loads(quiz.questions_json)
    q_dict = {q["id"]: q for q in questions_list}

    correct_count = 0
    total = len(questions_list)
    evaluations: List[QuestionEvaluation] = []

    for ans in payload.answers:
        q = q_dict.get(ans.question_id)
        if not q:
            continue

        selected = ans.selected_answer.strip()
        expected = q["correct_answer"].strip()
        is_corr = (selected.lower() == expected.lower())

        if is_corr:
            correct_count += 1

        evaluations.append(QuestionEvaluation(
            question_id=ans.question_id,
            question=q["question"],
            selected_answer=selected,
            correct_answer=expected,
            is_correct=is_corr,
            explanation=q.get("explanation", ""),
            citation=q.get("citation", "")
        ))

    percentage = round((correct_count / total * 100.0) if total > 0 else 0.0, 1)

    if percentage >= 80:
        feedback = "Outstanding performance! You have demonstrated strong mastery of this topic."
    elif percentage >= 60:
        feedback = "Good effort! You grasp the fundamentals, but reviewing explanations will solidify retention."
    else:
        feedback = "Deficit detected. This topic has been added to your revision alerts in Study Analytics."

    attempt_id = str(uuid.uuid4())
    attempt = QuizAttemptModel(
        id=attempt_id,
        quiz_id=quiz.id,
        score=correct_count,
        total_questions=total,
        percentage=percentage,
        topic=quiz.topic,
        difficulty=quiz.difficulty,
        answers_json=json.dumps([e.model_dump() for e in evaluations])
    )
    db.add(attempt)
    db.commit()

    return QuizResultResponse(
        attempt_id=attempt_id,
        quiz_id=quiz.id,
        score=correct_count,
        total_questions=total,
        percentage=percentage,
        topic=quiz.topic,
        difficulty=quiz.difficulty,
        feedback=feedback,
        evaluations=evaluations,
        completed_at=attempt.completed_at
    )


@router.get("/{quiz_id}", response_model=QuizResponse)
def get_quiz(quiz_id: str, db: Session = Depends(get_db)):
    """Fetch an existing quiz with questions."""
    quiz = db.query(QuizModel).filter(QuizModel.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")

    questions = [QuizQuestion(**q) for q in json.loads(quiz.questions_json)]
    return QuizResponse(
        id=quiz.id,
        document_id=quiz.document_id,
        title=quiz.title,
        topic=quiz.topic,
        difficulty=quiz.difficulty,
        question_count=quiz.question_count,
        questions=questions,
        created_at=quiz.created_at
    )
