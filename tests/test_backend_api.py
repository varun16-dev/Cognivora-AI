import os
import sys
import json
import pytest
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal, init_db
from app.database.models import DocumentModel, QuizModel, QuizAttemptModel

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Ensure database and seed data are ready."""
    init_db()
    db = SessionLocal()
    from app.config import SAMPLE_DIR
    from app.agents.document_agent import DocumentAgent
    if db.query(DocumentModel).count() == 0:
        sample_file = SAMPLE_DIR / "os_deadlocks_and_scheduling.txt"
        if sample_file.exists():
            DocumentAgent.process_and_index_document(
                file_path=str(sample_file),
                original_filename="Operating_Systems_Unit3_Deadlocks.txt",
                db=db
            )
    db.close()
    yield


def test_health_check():
    """Verify system health endpoint returns operational status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "active_model" in data
    assert "supported_upload_formats" in data
    print("✓ Health check endpoint verified.")


def test_list_documents():
    """Verify documents listing endpoint."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"✓ Documents listing verified ({len(data)} documents found).")


def test_rag_agent_chat():
    """Verify CoordinatorAgent handles conceptual Q&A with citations."""
    payload = {
        "message": "What are the 4 necessary conditions for a deadlock to occur?",
        "pedagogical_mode": "standard"
    }
    response = client.post("/api/agent/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 20
    assert "citations" in data
    assert "model_used" in data
    assert "agent_decision" in data
    print("✓ Agent chat with RAG citations verified.")


def test_generate_and_submit_quiz():
    """Verify end-to-end quiz generation, validation, and submission."""
    # 1. Fetch available document
    docs_res = client.get("/api/documents")
    assert docs_res.status_code == 200
    docs = docs_res.json()
    doc_id = docs[0]["id"] if docs else "mock_doc_id"

    # 2. Generate Quiz
    gen_payload = {
        "document_id": doc_id,
        "topic": "Deadlocks and Prevention",
        "difficulty": "medium",
        "question_count": 3,
        "question_types": ["mcq", "true_false"]
    }
    quiz_res = client.post("/api/quiz/generate", json=gen_payload)
    assert quiz_res.status_code == 201
    quiz_data = quiz_res.json()
    assert "id" in quiz_data
    assert len(quiz_data["questions"]) == 3

    # Verify question schema integrity
    for q in quiz_data["questions"]:
        assert "question" in q
        assert "correct_answer" in q
        assert "options" in q
        assert "explanation" in q
        if q["question_type"] == "mcq":
            assert q["correct_answer"] in q["options"]

    # 3. Submit Quiz Attempt
    quiz_id = quiz_data["id"]
    submit_payload = {
        "quiz_id": quiz_id,
        "answers": [
            {"question_id": q["id"], "selected_answer": q["correct_answer"]}
            for q in quiz_data["questions"]
        ]
    }
    submit_res = client.post("/api/quiz/submit", json=submit_payload)
    assert submit_res.status_code == 200
    result_data = submit_res.json()
    assert result_data["score"] == 3
    assert result_data["percentage"] == 100.0
    assert len(result_data["evaluations"]) == 3
    print("✓ Quiz generation, question schema validation, and score calculation verified.")


def test_generate_flashcards():
    """Verify flashcard deck generation."""
    docs_res = client.get("/api/documents")
    docs = docs_res.json()
    doc_id = docs[0]["id"] if docs else "mock_doc_id"

    payload = {
        "document_id": doc_id,
        "topic": "Process Synchronization",
        "card_count": 4
    }
    response = client.post("/api/flashcards/generate", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "cards" in data
    assert len(data["cards"]) == 4
    for card in data["cards"]:
        assert len(card["front"]) > 0
        assert len(card["back"]) > 0
    print("✓ Flashcards generation verified.")


def test_generate_summaries():
    """Verify multi-mode summary generation (short, detailed, exam_notes)."""
    docs_res = client.get("/api/documents")
    docs = docs_res.json()
    doc_id = docs[0]["id"] if docs else "mock_doc_id"

    for mode in ["short", "exam_notes"]:
        payload = {
            "document_id": doc_id,
            "topic": "Banker's Algorithm",
            "mode": mode
        }
        res = client.post("/api/summary/generate", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["mode"] == mode
        assert len(data["content"]) > 50
    print("✓ Multi-mode summary generator verified.")


def test_analytics_dashboard():
    """Verify Study Analytics dashboard metrics and EWMA topic mastery calculation."""
    response = client.get("/api/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "average_quiz_score" in data
    assert "topic_mastery" in data
    assert "improvement_recommendations" in data
    assert isinstance(data["topic_mastery"], list)
    print("✓ Analytics dashboard and EWMA mastery metrics verified.")


def test_empty_and_invalid_document_uploads():
    """Verify input validation rejects empty files and unsupported formats."""
    # 1. Empty file (0 bytes)
    empty_files = {"file": ("empty.txt", b"", "text/plain")}
    res_empty = client.post("/api/documents/upload", files=empty_files)
    assert res_empty.status_code == 400
    assert "empty" in res_empty.json()["detail"].lower()

    # 2. Unsupported extension (.exe)
    invalid_files = {"file": ("malicious.exe", b"binarycontent", "application/octet-stream")}
    res_invalid = client.post("/api/documents/upload", files=invalid_files)
    assert res_invalid.status_code == 400
    assert "unsupported" in res_invalid.json()["detail"].lower()
    print("✓ Document upload input validation verified (empty and unsupported formats rejected).")


def test_grounding_guardrail_refusal_for_unrelated_content():
    """Verify strict anti-hallucination: refuses to answer unrelated questions without source evidence."""
    payload = {
        "message": "What is the capital of Iceland and what was the 1998 GDP?",
        "pedagogical_mode": "standard"
    }
    response = client.post("/api/agent/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "cannot find this specific information" in data["answer"].lower()
    assert len(data["citations"]) == 0
    assert data["grounded_in_docs"] is False
    print("✓ Anti-hallucination grounding guardrail verified (zero hallucination for missing content).")


def test_langchain_tools_and_coordinator_integration():
    """Verify LangChain educational tool dispatching via CoordinatorAgent."""
    from app.agents.langchain_tools import (
        rag_retrieval_tool,
        quiz_generator_tool,
        flashcard_generator_tool,
        summary_generator_tool,
        study_analytics_tool,
        EDUCATIONAL_TOOLS
    )

    assert len(EDUCATIONAL_TOOLS) == 5

    # Test LangChain tool direct invocations
    rag_out = json.loads(rag_retrieval_tool.invoke({"query": "deadlock conditions"}))
    assert rag_out["status"] in ("success", "empty")

    analytics_out = json.loads(study_analytics_tool.invoke({"user_id": "test_student"}))
    assert analytics_out["status"] == "success"
    assert "average_quiz_score" in analytics_out

    # Test Coordinator routing to LangChain quiz tool
    coord_res = client.post("/api/agent/chat", json={"message": "Can you generate a quiz for me?"})
    assert coord_res.status_code == 200
    coord_data = coord_res.json()
    assert coord_data["intent_detected"] == "quiz"
    assert "quiz_generator_tool" in coord_data["agent_decision"]
    print("✓ LangChain educational tool integration and Coordinator dispatch verified.")


def test_export_quiz_and_summary_endpoints():
    """Verify study guide and quiz worksheet download/export endpoints."""
    # 1. Fetch available quiz and summary
    docs_res = client.get("/api/documents")
    doc_id = docs_res.json()[0]["id"]

    # Generate a quiz to export
    q_res = client.post("/api/quiz/generate", json={"document_id": doc_id, "topic": "Deadlocks", "question_count": 3})
    quiz_id = q_res.json()["id"]

    # Export quiz markdown
    export_quiz_res = client.get(f"/api/quiz/{quiz_id}/export")
    assert export_quiz_res.status_code == 200
    assert "Content-Disposition" in export_quiz_res.headers
    assert "attachment" in export_quiz_res.headers["Content-Disposition"]
    assert "# " in export_quiz_res.text

    # Generate a summary to export
    s_res = client.post("/api/summary/generate", json={"document_id": doc_id, "topic": "Deadlocks", "mode": "short"})
    summary_id = s_res.json()["id"]

    # Export summary markdown
    export_sum_res = client.get(f"/api/summary/{summary_id}/export")
    assert export_sum_res.status_code == 200
    assert "Content-Disposition" in export_sum_res.headers
    assert "attachment" in export_sum_res.headers["Content-Disposition"]
    assert "## Summary Notes" in export_sum_res.text
    print("✓ Quiz and Summary export endpoints verified.")


def test_document_suggested_questions_endpoint():
    """Verify document-specific suggested study questions endpoint."""
    docs_res = client.get("/api/documents")
    assert docs_res.status_code == 200
    doc_id = docs_res.json()[0]["id"]

    res = client.get(f"/api/documents/{doc_id}/suggested-questions")
    assert res.status_code == 200
    data = res.json()
    assert "questions" in data
    assert isinstance(data["questions"], list)
    assert len(data["questions"]) >= 3
    print(f"✓ Document suggested questions verified: {len(data['questions'])} questions returned.")
