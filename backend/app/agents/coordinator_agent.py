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
from app.agents.langchain_tools import (
    rag_retrieval_tool,
    quiz_generator_tool,
    flashcard_generator_tool,
    summary_generator_tool,
    study_analytics_tool,
    EDUCATIONAL_TOOLS,
    EDUCATIONAL_TOOLS_BY_NAME
)

logger = logging.getLogger("CognivoraAI.CoordinatorAgent")


class CoordinatorAgent:
    """
    Central Orchestration Agent.
    Understands student queries, classifies pedagogical intent,
    autonomously selects and executes specialized educational tools/agents
    using LangChain tool abstractions, and logs every decision with execution telemetry.
    """

    # Registered LangChain tools available to this Coordinator
    tools = EDUCATIONAL_TOOLS

    @staticmethod
    def handle_student_interaction(
        message: str,
        document_id: Optional[str] = None,
        pedagogical_mode: str = "standard",
        db: Session = None
    ) -> ChatMessageResponse:
        """
        Coordinates full multi-agent reasoning, LangChain tool dispatch, and RAG answer synthesis.
        """
        start_time = time.time()
        logger.info(f"[CoordinatorAgent] Received student message: '{message}' (mode={pedagogical_mode})")

        # 1. Autonomous Intent Classification & Tool Selection
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
        grounded_in_docs = False

        try:
            if intent == "quiz":
                decision_rationale = "Student requested assessment practice. Selected and executed LangChain 'quiz_generator_tool'."
                tools_called = ["quiz_generator_tool"]
                
                # Derive topic dynamically from document or student query
                quiz_topic = doc_record.subject if (doc_record and doc_record.subject) else "Core Concepts"

                tool_res_raw = quiz_generator_tool.invoke({
                    "topic": quiz_topic,
                    "difficulty": "medium",
                    "question_count": 5,
                    "document_id": document_id
                })
                tool_data = json.loads(tool_res_raw)
                answer = (
                    f"🎯 **Diagnostic Quiz Generated!**\n\n"
                    f"I have created a 5-question practice quiz titled **'{tool_data.get('title', 'Course Assessment')}'** grounded in your course notes.\n"
                    f"Navigate to the **Quiz Generator** tab in the sidebar to attempt the quiz with an interactive timer and instant feedback."
                )
                grounded_in_docs = True

            elif intent == "flashcard":
                decision_rationale = "Student requested memory reinforcement. Selected and executed LangChain 'flashcard_generator_tool'."
                tools_called = ["flashcard_generator_tool"]
                tool_res_raw = flashcard_generator_tool.invoke({
                    "topic": "Core Concepts",
                    "card_count": 6,
                    "document_id": document_id
                })
                tool_data = json.loads(tool_res_raw)
                answer = (
                    f"🃏 **Flashcard Deck Generated!**\n\n"
                    f"I have created the **'{tool_data.get('title', 'Active Recall Deck')}'** deck with 6 revision cards.\n"
                    f"Navigate to the **Flashcards** tab to study with 3D flip animations and spaced-repetition ratings."
                )
                grounded_in_docs = True

            elif intent == "summary":
                decision_rationale = "Student requested conceptual overview. Selected and executed LangChain 'summary_generator_tool'."
                tools_called = ["summary_generator_tool"]
                tool_res_raw = summary_generator_tool.invoke({
                    "topic": "Chapter Overview",
                    "mode": "detailed",
                    "document_id": document_id
                })
                tool_data = json.loads(tool_res_raw)
                answer = (
                    f"📝 **Summary Generated!**\n\n"
                    f"### {tool_data.get('title', 'Chapter Summary')}\n\n"
                    f"{tool_data.get('content', '')}\n\n"
                    f"💡 *Tip:* You can also listen to this as an audio lesson in the **Audio Learning** tab."
                )
                grounded_in_docs = True

            elif intent == "analytics":
                decision_rationale = "Student inquired about mastery or weaknesses. Selected and executed LangChain 'study_analytics_tool'."
                tools_called = ["study_analytics_tool"]
                tool_res_raw = study_analytics_tool.invoke({"user_id": "student_default"})
                tool_data = json.loads(tool_res_raw)
                weak_list = ", ".join(tool_data.get("weak_topics", [])) if tool_data.get("weak_topics") else "None (<60% threshold)"
                avg_score = tool_data.get("average_quiz_score", 75.0)
                answer = (
                    f"📊 **Student Mastery Diagnostic:**\n\n"
                    f"- **Overall Average Score:** {avg_score}%\n"
                    f"- **Identified Weak Topics:** {weak_list}\n"
                    f"- **Recommended Next Action:** Take an adaptive practice quiz on your lowest-scoring topic to reinforce retention."
                )
                grounded_in_docs = True

            else:
                # Default: Grounded Q&A via LangChain RAG Retrieval Tool
                decision_rationale = f"Conceptual inquiry detected. Selected LangChain 'rag_retrieval_tool' and Gemini synthesis engine (mode={pedagogical_mode})."
                tools_called = ["rag_retrieval_tool", "GeminiService.generate_grounded_answer"]

                # 1. Retrieve RAG chunks via LangChain tool
                rag_res_raw = rag_retrieval_tool.invoke({
                    "query": message,
                    "document_id": document_id
                })
                rag_data = json.loads(rag_res_raw)
                
                # Fetch full chunk objects from DocumentAgent
                chunks = DocumentAgent.retrieve_grounded_context(
                    query=message,
                    document_id=document_id,
                    top_k=4
                )

                # Strict Grounding Check:
                # If no chunks found, similarity is too low, or non-stopword query tokens have zero overlap with curriculum text
                stop_words = {"what", "is", "the", "and", "was", "for", "in", "of", "a", "an", "to", "how", "why", "are", "do", "does", "can", "you", "tell", "me", "about"}
                q_tokens = set(re.findall(r"\w+", message.lower())) - stop_words
                top_text = (chunks[0].get("text", "") if chunks else "").lower()
                has_keyword_match = any(t in top_text for t in q_tokens) if q_tokens else True

                is_irrelevant = (not chunks) or (chunks[0].get("similarity_score", 0.0) < 0.45 and not has_keyword_match) or (not has_keyword_match and chunks[0].get("similarity_score", 0.0) < 0.65)

                if is_irrelevant:
                    answer = (
                        "I cannot find this specific information in your uploaded course materials. "
                        "Please upload relevant notes or consult your professor."
                    )
                    model_used = "Cognivora Grounding Guardrail"
                    is_demo_mode = not gemini_service.is_live()
                    grounded_in_docs = False
                else:
                    # Format citations only for genuinely relevant chunks
                    for c in chunks:
                        if c.get("similarity_score", 0.0) >= 0.20:
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
                    model_used = llm_res.get("model_used", "Gemini 3.5 Flash")
                    is_demo_mode = llm_res.get("is_demo_mode", False)
                    if "cannot find this specific information" in answer.lower():
                        citations = []
                        grounded_in_docs = False
                    else:
                        grounded_in_docs = len(citations) > 0

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
            grounded_in_docs=grounded_in_docs
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
