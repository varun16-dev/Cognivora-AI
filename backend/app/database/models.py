import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DocumentModel(Base):
    """Uploaded academic document metadata."""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    subject = Column(String(100), default="General Studies")
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    chunk_count = Column(Integer, default=0)
    topics_json = Column(Text, default="[]")  # List of extracted topics
    summary = Column(Text, nullable=True)
    processing_status = Column(String(20), default="processed")  # processing, processed, error
    error_message = Column(Text, nullable=True)

    quizzes = relationship("QuizModel", back_populates="document", cascade="all, delete-orphan")
    flashcards = relationship("FlashcardDeckModel", back_populates="document", cascade="all, delete-orphan")
    summaries = relationship("SummaryModel", back_populates="document", cascade="all, delete-orphan")


class QuizModel(Base):
    """Generated educational quiz."""
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    topic = Column(String(150), default="General")
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    question_count = Column(Integer, default=5)
    questions_json = Column(Text, nullable=False)  # Array of QuizQuestion dicts
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentModel", back_populates="quizzes")
    attempts = relationship("QuizAttemptModel", back_populates="quiz", cascade="all, delete-orphan")


class QuizAttemptModel(Base):
    """Student submission of a quiz attempt."""
    __tablename__ = "quiz_attempts"

    id = Column(String(36), primary_key=True, index=True)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    topic = Column(String(150), default="General")
    difficulty = Column(String(20), default="medium")
    answers_json = Column(Text, nullable=False)  # Student answers & feedback
    completed_at = Column(DateTime, default=datetime.utcnow)

    quiz = relationship("QuizModel", back_populates="attempts")


class FlashcardDeckModel(Base):
    """Generated flashcard collection."""
    __tablename__ = "flashcard_decks"

    id = Column(String(36), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    topic = Column(String(150), default="General")
    cards_json = Column(Text, nullable=False)  # Array of Flashcard dicts
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentModel", back_populates="flashcards")


class SummaryModel(Base):
    """Generated educational summaries."""
    __tablename__ = "summaries"

    id = Column(String(36), primary_key=True, index=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    topic = Column(String(150), default="General")
    mode = Column(String(50), default="detailed")  # short, detailed, key_points, beginner, exam_notes
    content = Column(Text, nullable=False)
    key_points_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentModel", back_populates="summaries")


class AgentLogModel(Base):
    """Audit log of Agentic decisions, routing, and tool invocations."""
    __tablename__ = "agent_logs"

    id = Column(String(36), primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    agent_name = Column(String(50), nullable=False)  # CoordinatorAgent, QuizAgent, etc.
    user_query = Column(Text, nullable=False)
    detected_intent = Column(String(50), nullable=False)  # qa, quiz, flashcard, summary, analytics
    decision_rationale = Column(Text, nullable=False)
    tools_invoked = Column(Text, default="[]")  # JSON list of tools
    execution_time_ms = Column(Float, default=0.0)
    status = Column(String(20), default="success")  # success, error, fallback
    output_summary = Column(Text, nullable=True)
