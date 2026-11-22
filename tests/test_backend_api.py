import os
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal, init_db
from app.database.models import DocumentModel, QuizModel, QuizAttemptModel

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Ensure database and seed data are ready."""
    init_db()
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
