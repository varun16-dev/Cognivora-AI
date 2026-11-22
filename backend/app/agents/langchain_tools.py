import json
import logging
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from app.services.rag_engine import rag_engine
from app.agents.quiz_agent import QuizAgent
from app.agents.flashcard_agent import FlashcardAgent
from app.agents.summary_agent import SummaryAgent
from app.services.analytics_service import AnalyticsService
from app.database.session import SessionLocal

logger = logging.getLogger("CognivoraAI.LangChainTools")


@tool
def rag_retrieval_tool(query: str, document_id: Optional[str] = None) -> str:
    """
    Retrieves syllabus-grounded context chunks and page citations from ChromaDB
    for a given student educational query or topic.
    """
    logger.info(f"[LangChain:rag_retrieval_tool] Query: '{query}', Document: '{document_id}'")
    chunks = rag_engine.retrieve_relevant_chunks(query=query, document_id=document_id, top_k=4)
    if not chunks:
        return json.dumps({
            "status": "empty",
            "message": "No relevant course material found for query.",
            "chunks": []
        })

    serialized_chunks = [
        {
            "document_name": c.get("document_name", "Academic Note"),
            "page_number": int(c.get("page_number", 1)),
            "similarity_score": float(c.get("similarity_score", 0.0)),
            "excerpt": str(c.get("text", "")[:350])
        }
        for c in chunks
    ]
    return json.dumps({"status": "success", "count": len(chunks), "chunks": serialized_chunks})


@tool
def quiz_generator_tool(
    topic: str,
    difficulty: str = "medium",
    question_count: int = 5,
    document_id: Optional[str] = None
) -> str:
    """
    Generates a structured, calibrated educational assessment (MCQ, True/False, Fill-in-Blank)
    grounded in uploaded course materials with Bloom's taxonomy difficulty weighting.
    """
    logger.info(f"[LangChain:quiz_generator_tool] Generating {question_count} {difficulty} questions on '{topic}'")
    db = SessionLocal()
    try:
        quiz = QuizAgent.generate_quiz(
            document_id=document_id or "default_doc",
            document_name="Course Curriculum",
            topic=topic,
            difficulty=difficulty,
            question_count=question_count,
            question_types=["mcq", "true_false", "fill_blank"],
            db=db
        )
        return json.dumps({
            "status": "success",
            "quiz_id": quiz.id,
            "title": quiz.title,
            "topic": quiz.topic,
            "difficulty": quiz.difficulty,
            "question_count": quiz.question_count
        })
    finally:
        db.close()


@tool
def flashcard_generator_tool(
    topic: str,
    card_count: int = 6,
    document_id: Optional[str] = None
) -> str:
    """
    Generates an interactive 3D active-recall flashcard deck with front-back question-answer pairs
    and spaced-repetition confidence ratings.
    """
    logger.info(f"[LangChain:flashcard_generator_tool] Generating {card_count} flashcards on '{topic}'")
    db = SessionLocal()
    try:
        deck = FlashcardAgent.generate_deck(
            document_id=document_id or "default_doc",
            document_name="Course Curriculum",
            topic=topic,
            card_count=card_count,
            db=db
        )
        return json.dumps({
            "status": "success",
            "deck_id": deck.id,
            "title": deck.title,
            "topic": deck.topic,
            "card_count": deck.card_count
        })
    finally:
        db.close()


@tool
def summary_generator_tool(
    topic: str,
    mode: str = "detailed",
    document_id: Optional[str] = None
) -> str:
    """
    Generates an educational summary in one of 5 pedagogical modes:
    short (executive summary), detailed (deep-dive), key_points (bulleted takeaways),
    beginner (ELI5 with analogies), or exam_notes (high-yield revision).
    """
    logger.info(f"[LangChain:summary_generator_tool] Generating {mode} summary on '{topic}'")
    db = SessionLocal()
    try:
        summary_rec = SummaryAgent.generate_summary(
            document_id=document_id or "default_doc",
            document_name="Course Curriculum",
            topic=topic,
            mode=mode,
            db=db
        )
        return json.dumps({
            "status": "success",
            "summary_id": summary_rec.id,
            "title": summary_rec.title,
            "mode": summary_rec.mode,
            "content": summary_rec.content,
            "key_points": json.loads(summary_rec.key_points_json) if summary_rec.key_points_json else []
        })
    finally:
        db.close()


@tool
def study_analytics_tool(user_id: str = "student_default") -> str:
    """
    Queries student quiz performance history, calculates Exponentially Weighted Moving Average (EWMA)
    topic mastery scores, and returns targeted revision recommendations for topics below 60%.
    """
    logger.info(f"[LangChain:study_analytics_tool] Computing analytics for {user_id}")
    db = SessionLocal()
    try:
        metrics = AnalyticsService.get_dashboard_metrics(db=db)
        return json.dumps({
            "status": "success",
            "total_quizzes_attempted": metrics.total_quizzes_attempted,
            "average_quiz_score": metrics.average_quiz_score,
            "weak_topics": metrics.weak_topics,
            "total_documents": metrics.total_documents
        })
    finally:
        db.close()


# Registered LangChain Educational Tools
EDUCATIONAL_TOOLS = [
    rag_retrieval_tool,
    quiz_generator_tool,
    flashcard_generator_tool,
    summary_generator_tool,
    study_analytics_tool,
]

EDUCATIONAL_TOOLS_BY_NAME = {t.name: t for t in EDUCATIONAL_TOOLS}
