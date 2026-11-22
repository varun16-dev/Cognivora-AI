from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# Document Schemas
# ==============================================================================
class TopicHierarchy(BaseModel):
    name: str
    level: int = 1
    subtopics: List[str] = Field(default_factory=list)


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    subject: str
    upload_timestamp: datetime
    chunk_count: int
    topics: List[str]
    processing_status: str
    summary: Optional[str] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentHierarchyResponse(BaseModel):
    document_id: str
    filename: str
    subject: str
    topics: List[TopicHierarchy]


# ==============================================================================
# RAG & Citation Schemas
# ==============================================================================
class Citation(BaseModel):
    document_id: str
    document_name: str
    page_number: Optional[int] = 1
    chunk_index: int
    similarity_score: float
    excerpt: str


class ChatMessageRequest(BaseModel):
    message: str
    document_id: Optional[str] = None
    pedagogical_mode: str = "standard"  # standard, explain_simply, exam_cram, deep_dive
    session_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    agent_decision: Optional[str] = None
    intent_detected: Optional[str] = None
    model_used: str
    is_demo_mode: bool = False
    grounded_in_docs: bool = True


# ==============================================================================
# Quiz Schemas
# ==============================================================================
class QuizQuestion(BaseModel):
    id: int
    question: str
    question_type: str = "mcq"  # mcq, true_false, fill_blank
    options: List[str] = Field(default_factory=list)
    correct_answer: str
    explanation: str
    topic: str = "General"
    difficulty: str = "medium"
    citation: Optional[str] = None


class QuizGenerateRequest(BaseModel):
    document_id: str
    topic: Optional[str] = None
    difficulty: str = "medium"  # easy, medium, hard
    question_count: int = Field(default=5, ge=1, le=20)
    question_types: List[str] = Field(default_factory=lambda: ["mcq"])  # mcq, true_false, fill_blank


class QuizResponse(BaseModel):
    id: str
    document_id: str
    title: str
    topic: str
    difficulty: str
    question_count: int
    questions: List[QuizQuestion]
    created_at: datetime


class StudentAnswer(BaseModel):
    question_id: int
    selected_answer: str


class QuizSubmitRequest(BaseModel):
    quiz_id: str
    answers: List[StudentAnswer]


class QuestionEvaluation(BaseModel):
    question_id: int
    question: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str
    citation: Optional[str] = None


class QuizResultResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    score: int
    total_questions: int
    percentage: float
    topic: str
    difficulty: str
    feedback: str
    evaluations: List[QuestionEvaluation]
    completed_at: datetime


# ==============================================================================
# Flashcard Schemas
# ==============================================================================
class Flashcard(BaseModel):
    id: int
    front: str  # Concept or Question
    back: str   # Definition, Core Answer, Explanation
    topic: str = "General"
    difficulty: str = "medium"
    mastery_status: str = "learning"  # learning, reviewing, mastered


class FlashcardDeckGenerateRequest(BaseModel):
    document_id: str
    topic: Optional[str] = None
    card_count: int = Field(default=6, ge=3, le=20)


class FlashcardDeckResponse(BaseModel):
    id: str
    document_id: str
    title: str
    topic: str
    card_count: int
    cards: List[Flashcard]
    created_at: datetime


# ==============================================================================
# Summary Schemas
# ==============================================================================
class SummaryGenerateRequest(BaseModel):
    document_id: str
    topic: Optional[str] = None
    mode: str = "detailed"  # short, detailed, key_points, beginner, exam_notes


class SummaryResponse(BaseModel):
    id: str
    document_id: str
    title: str
    topic: str
    mode: str
    content: str
    key_points: List[str] = Field(default_factory=list)
    created_at: datetime


# ==============================================================================
# Analytics & Dashboard Schemas
# ==============================================================================
class TopicMasteryItem(BaseModel):
    topic: str
    subject: str
    mastery_percentage: float
    status: str  # mastered, developing, weak
    total_questions: int
    correct_count: int
    recommended_action: str


class QuizHistoryItem(BaseModel):
    attempt_id: str
    quiz_title: str
    topic: str
    difficulty: str
    score: int
    total: int
    percentage: float
    completed_at: datetime


class AnalyticsDashboardResponse(BaseModel):
    total_documents: int
    total_quizzes_attempted: int
    average_quiz_score: float
    total_flashcards_created: int
    total_summaries_generated: int
    topic_mastery: List[TopicMasteryItem]
    recent_quiz_history: List[QuizHistoryItem]
    weak_topics: List[str]
    improvement_recommendations: List[str]


# ==============================================================================
# Agent Telemetry Log Schema
# ==============================================================================
class AgentLogResponse(BaseModel):
    id: str
    timestamp: datetime
    agent_name: str
    user_query: str
    detected_intent: str
    decision_rationale: str
    tools_invoked: List[str]
    execution_time_ms: float
    status: str
    output_summary: Optional[str] = None
