import time
import json
import uuid
import re
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.services.gemini_client import gemini_service
from app.agents.document_agent import DocumentAgent
from app.agents.quiz_agent import QuizAgent
from app.agents.flashcard_agent import FlashcardAgent
from app.agents.summary_agent import SummaryAgent
from app.services.analytics_service import AnalyticsService
from app.database.models import AgentLogModel, DocumentModel
from app.schemas.schemas import ChatMessageResponse, Citation

logger = logging.getLogger("CognivoraAI.CoordinatorAgent")


class CoordinatorAgent:
    """
    Central Orchestration Agent.
    Understands student queries, classifies pedagogical intent,
    autonomously selects and executes specialized educational tools/agents,
    and logs every decision with execution telemetry.
    """

    @staticmethod
    def handle_student_interaction(
        message: str,
        document_id: Optional[str] = None,
        pedagogical_mode: str = "standard",
        db: Session = None
    ) -> ChatMessageResponse:
        """
        Coordinates full multi-agent reasoning, tool dispatch, and RAG answer synthesis.
        """
        start_time = time.time()
        logger.info(f"[CoordinatorAgent] Received student message: '{message}' (mode={pedagogical_mode})")

        # 1. Autonomous Intent Classification
        intent = CoordinatorAgent._classify_intent(message)
        decision_rationale = ""
        tools_called = []
        status = "success"

        # If document_id not provided, pick the most recently uploaded document if available
        doc_record = None
        if db:
            if document_id:
                doc_record = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
            if not doc_record:
                doc_record = db.query(DocumentModel).order_by(DocumentModel.upload_timestamp.desc()).first()
                if doc_record:
                    document_id = doc_record.id

        doc_name = doc_record.filename if doc_record else "Course Curriculum"

        citations: List[Citation] = []
        answer = ""
        model_used = "Gemini 2.5 Flash"
        is_demo_mode = False

        try:
            if intent == "quiz":
                decision_rationale = "Student requested assessment practice. Dispatched to QuizAgent for calibrated question generation."
                tools_called = ["RAGRetrievalTool", "QuizGenerationTool"]
                quiz = QuizAgent.generate_quiz(
                    document_id=document_id or "default_doc",
                    document_name=doc_name,
                    topic="Deadlocks & Scheduling",
                    difficulty="medium",
                    question_count=5,
                    db=db
                )
                answer = (
                    f"🎯 **Diagnostic Quiz Generated!**\n\n"
                    f"I have created a 5-question practice quiz titled **'{quiz.title}'** grounded in your course notes.\n"
                    f"Navigate to the **Quiz Generator** tab in the sidebar to attempt the quiz with interactive timer and instant feedback."
                )

            elif intent == "flashcard":
                decision_rationale = "Student requested memory reinforcement. Dispatched to FlashcardAgent for spaced-repetition deck generation."
                tools_called = ["RAGRetrievalTool", "FlashcardGenerationTool"]
                deck = FlashcardAgent.generate_deck(
                    document_id=document_id or "default_doc",
                    document_name=doc_name,
                    topic="Core Concepts",
                    card_count=6,
                    db=db
                )
                answer = (
                    f"🃏 **Flashcard Deck Generated!**\n\n"
                    f"I have created the **'{deck.title}'** deck with 6 revision cards.\n"
                    f"Navigate to the **Flashcards** tab to study with 3D flip animations and Leitner review intervals."
                )

            elif intent == "summary":
                decision_rationale = "Student requested conceptual overview. Dispatched to SummaryAgent for multi-mode note synthesis."
                tools_called = ["RAGRetrievalTool", "SummaryGenerationTool"]
                summary_record = SummaryAgent.generate_summary(
                    document_id=document_id or "default_doc",
                    document_name=doc_name,
                    topic="Chapter Overview",
                    mode="detailed",
                    db=db
                )
                answer = (
                    f"📝 **Summary Generated!**\n\n"
                    f"### {summary_record.title}\n\n"
                    f"{summary_record.content}\n\n"
                    f"💡 *Tip:* You can also listen to this as an audio lesson in the **Audio Learning** tab."
                )

            elif intent == "analytics":
                decision_rationale = "Student inquired about mastery or weaknesses. Dispatched to AnalyticsService."
                tools_called = ["LearnerAnalyticsEngine", "TopicMasteryCalculation"]
                dashboard_data = AnalyticsService.get_dashboard_metrics(db) if db else None
                weak_list = ", ".join(dashboard_data.weak_topics) if dashboard_data and dashboard_data.weak_topics else "None (<60% threshold)"
                avg_score = dashboard_data.average_quiz_score if dashboard_data else 75.0
                answer = (
                    f"📊 **Student Mastery Diagnostic:**\n\n"
                    f"- **Overall Average Score:** {avg_score}%\n"
                    f"- **Identified Weak Topics:** {weak_list}\n"
                    f"- **Recommended Next Action:** Take an adaptive practice quiz on your lowest-scoring topic to reinforce retention."
                )

            else:
                # Default: Grounded Q&A via RAG
                decision_rationale = f"Conceptual inquiry detected. Dispatched to DocumentAgent for vector retrieval and Gemini for grounded synthesis (mode={pedagogical_mode})."
                tools_called = ["DocumentAgent.retrieve_grounded_context", "GeminiService.generate_grounded_answer"]

                # 1. Retrieve RAG chunks
                chunks = DocumentAgent.retrieve_grounded_context(
                    query=message,
                    document_id=document_id,
                    top_k=4
                )

                # 2. Format citations
                for c in chunks:
                    citations.append(Citation(
                        document_id=c.get("document_id", document_id or ""),
                        document_name=c.get("document_name", doc_name),
                        page_number=c.get("page_number", 1),
                        chunk_index=c.get("chunk_index", 0),
                        similarity_score=c.get("similarity_score", 0.8),
                        excerpt=c.get("text", "")[:250] + "..."
                    ))

                # 3. Generate grounded response
                llm_res = gemini_service.generate_grounded_answer(
                    prompt=message,
                    context_chunks=chunks,
                    pedagogical_mode=pedagogical_mode
                )
                answer = llm_res.get("answer", "")
                model_used = llm_res.get("model_used", "Gemini 2.5 Flash")
                is_demo_mode = llm_res.get("is_demo_mode", False)

        except Exception as e:
            logger.error(f"[CoordinatorAgent] Execution failure: {e}")
            status = "error"
            decision_rationale += f" | Failure recovered via safety fallback: {str(e)}"
            answer = f"I encountered an error processing your request: {str(e)}. Please retry."

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        # 4. Telemetry Logging to SQLite Database
        if db:
            try:
                log_record = AgentLogModel(
                    id=str(uuid.uuid4()),
                    agent_name="CoordinatorAgent",
                    user_query=message,
                    detected_intent=intent,
                    decision_rationale=decision_rationale,
                    tools_invoked=json.dumps(tools_called),
                    execution_time_ms=elapsed_ms,
                    status=status,
                    output_summary=answer[:150] + "..."
                )
                db.add(log_record)
                db.commit()
            except Exception as log_err:
                logger.warning(f"Failed to record agent log: {log_err}")

        return ChatMessageResponse(
            answer=answer,
            citations=citations,
            agent_decision=decision_rationale,
            intent_detected=intent,
            model_used=model_used,
            is_demo_mode=is_demo_mode,
            grounded_in_docs=len(citations) > 0 or intent != "qa"
        )

    @staticmethod
    def _classify_intent(query: str) -> str:
        """
        Determines user intent from natural language keywords and linguistic patterns.
        """
        q = query.lower()
        if re.search(r"\b(quiz|test|mcq|assessment|exam question|questions for)\b", q):
            return "quiz"
        elif re.search(r"\b(flashcard|flash cards|revision card|anki|cards for)\b", q):
            return "flashcard"
        elif re.search(r"\b(summary|summarize|overview|bullet points|brief|explain chapter)\b", q):
            return "summary"
        elif re.search(r"\b(mastery|analytics|my score|weakness|progress|how am i doing|streak)\b", q):
            return "analytics"
        else:
            return "qa"
