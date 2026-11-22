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
from app.database.models import DocumentModel, QuizModel
from app.agents.document_agent import DocumentAgent
from app.services.rag_engine import rag_engine

client = TestClient(app)

# Sample texts for isolation regression testing
OS_TEXT = """## Subject: Operating Systems
### Chapter: Process Management and Deadlocks

A deadlock in an operating system occurs when two or more processes are unable to proceed because each is waiting for the other to release a resource.
The four necessary conditions for deadlock (Coffman conditions) are:
1. Mutual Exclusion: At least one resource must be held in a non-shareable mode.
2. Hold and Wait: A process must be holding at least one resource and waiting to acquire additional resources.
3. No Preemption: Resources cannot be preempted; a resource can only be released voluntarily by the process holding it.
4. Circular Wait: A closed chain of processes exists, where each process holds at least one resource needed by the next.

Dijkstra's Banker's Algorithm is a classic deadlock avoidance strategy. It tracks maximum resource claims and tests for safe state sequences before allocating resources.
The Ostrich Algorithm is a strategy of ignoring deadlocks under the assumption that they occur rarely enough that system reboot is cheaper than prevention overhead.
"""

CRYPTO_TEXT = """## Subject: Data Security and Privacy
### Chapter: Network Model and Classical Encryption Techniques

Data security relies on cryptography to ensure confidentiality, integrity, and authenticity.
Classical encryption techniques primarily utilize symmetric-key cryptography, where the sender and receiver share a secret key.
In substitution ciphers, characters in the plaintext are replaced by other characters, symbols, or numbers.
The Caesar Cipher is an elementary substitution cipher where each letter in the plaintext is shifted down the alphabet by a fixed integer key k.
Mathematically, the Caesar encryption transformation is defined as:
E(p) = (p + k) mod 26
Decryption reverses the shift using the formula:
D(c) = (c - k) mod 26
Monoalphabetic ciphers use a fixed substitution over the entire message, making them vulnerable to frequency analysis of letter occurrences.
Polyalphabetic ciphers, such as the Vigenère cipher, use multiple substitution alphabets based on a repeating keyword to flatten letter frequency distributions.
"""


@pytest.fixture(scope="module")
def setup_two_documents(tmp_path_factory):
    """Creates and indexes two distinct educational documents for regression isolation tests."""
    init_db()
    db = SessionLocal()

    temp_dir = tmp_path_factory.mktemp("test_docs")

    # Document 1: Operating Systems
    os_file = temp_dir / "Operating_Systems_Unit3.txt"
    os_file.write_text(OS_TEXT, encoding="utf-8")
    doc_os = DocumentAgent.process_and_index_document(
        file_path=str(os_file),
        original_filename="Operating_Systems_Unit3.txt",
        db=db
    )

    # Document 2: Data Security and Privacy
    crypto_file = temp_dir / "LectureNotes_BAD703_Data_Security_and_Privacy.txt"
    crypto_file.write_text(CRYPTO_TEXT, encoding="utf-8")
    doc_crypto = DocumentAgent.process_and_index_document(
        file_path=str(crypto_file),
        original_filename="LectureNotes_BAD703_Data_Security_and_Privacy.txt",
        db=db
    )

    doc_os_id = doc_os.id
    doc_crypto_id = doc_crypto.id
    db.close()

    yield {
        "os_id": doc_os_id,
        "os_name": "Operating_Systems_Unit3.txt",
        "crypto_id": doc_crypto_id,
        "crypto_name": "LectureNotes_BAD703_Data_Security_and_Privacy.txt"
    }


def test_rag_retrieval_strict_document_isolation(setup_two_documents):
    """Verify that RAG chunk retrieval never leaks chunks across different document IDs."""
    data = setup_two_documents
    crypto_id = data["crypto_id"]
    os_id = data["os_id"]

    # Retrieve chunks targeting Data Security document
    crypto_chunks = rag_engine.retrieve_relevant_chunks(
        query="Caesar cipher substitution encryption techniques",
        document_id=crypto_id,
        top_k=4
    )
    assert len(crypto_chunks) > 0, "Should retrieve chunks from Data Security document"
    for c in crypto_chunks:
        assert c["document_id"] == crypto_id, f"Cross-contamination detected: expected {crypto_id}, got {c['document_id']}"
        assert "deadlock" not in c["text"].lower(), "Deadlock content leaked into Data Security chunks"
        assert "banker" not in c["text"].lower(), "Banker's algorithm leaked into Data Security chunks"

    # Retrieve chunks targeting Operating Systems document
    os_chunks = rag_engine.retrieve_relevant_chunks(
        query="Deadlock four conditions Coffman Banker",
        document_id=os_id,
        top_k=4
    )
    assert len(os_chunks) > 0, "Should retrieve chunks from Operating Systems document"
    for c in os_chunks:
        assert c["document_id"] == os_id, f"Cross-contamination detected: expected {os_id}, got {c['document_id']}"
        assert "caesar" not in c["text"].lower(), "Caesar cipher leaked into Operating Systems chunks"
        assert "substitution" not in c["text"].lower(), "Substitution cipher leaked into Operating Systems chunks"


def test_quiz_generator_data_security_document_isolation(setup_two_documents):
    """
    REGRESSION TEST: Verify selecting Data Security document generates questions exclusively
    about encryption, ciphers, and security, with ZERO Operating Systems questions.
    """
    data = setup_two_documents
    crypto_id = data["crypto_id"]
    crypto_name = data["crypto_name"]

    payload = {
        "document_id": crypto_id,
        "topic": "Classical Encryption Techniques",
        "difficulty": "medium",
        "question_count": 5,
        "question_types": ["mcq", "true_false"]
    }

    res = client.post("/api/quiz/generate", json=payload)
    assert res.status_code == 201, f"Quiz generation failed: {res.text}"
    quiz = res.json()

    assert quiz["document_id"] == crypto_id
    assert len(quiz["questions"]) == 5

    # Check question content for absolute topic isolation
    forbidden_os_terms = ["deadlock", "banker's algorithm", "ostrich algorithm", "coffman", "hold and wait", "circular wait"]
    required_security_terms = ["cipher", "encrypt", "substitution", "caesar", "key", "secur", "crypt", "frequency"]

    found_security_concepts = False
    for q in quiz["questions"]:
        full_text = (
            f"{q['question']} {' '.join(q.get('options', []))} {q.get('explanation', '')}"
        ).lower()

        # Strict check: NO OS Deadlock questions allowed
        for bad_term in forbidden_os_terms:
            assert bad_term not in full_text, (
                f"Contamination bug reproduced: Found OS term '{bad_term}' in Data Security quiz question: {q['question']}"
            )

        if any(term in full_text for term in required_security_terms):
            found_security_concepts = True

        # Citation must reference Data Security document
        citation = q.get("citation", "")
        assert "Operating_Systems" not in citation, f"Citation references wrong document: {citation}"

    assert found_security_concepts, "Quiz questions must reflect Data Security curriculum content."


def test_quiz_generator_operating_systems_isolation(setup_two_documents):
    """Verify selecting Operating Systems generates questions on deadlocks and scheduling."""
    data = setup_two_documents
    os_id = data["os_id"]

    payload = {
        "document_id": os_id,
        "topic": "Deadlocks and Process Synchronization",
        "difficulty": "medium",
        "question_count": 5,
        "question_types": ["mcq", "true_false"]
    }

    res = client.post("/api/quiz/generate", json=payload)
    assert res.status_code == 201, f"Quiz generation failed: {res.text}"
    quiz = res.json()

    assert quiz["document_id"] == os_id
    assert len(quiz["questions"]) == 5

    forbidden_crypto_terms = ["caesar", "cipher", "vigenère", "plaintext", "substitution"]
    for q in quiz["questions"]:
        full_text = (
            f"{q['question']} {' '.join(q.get('options', []))} {q.get('explanation', '')}"
        ).lower()

        for bad_term in forbidden_crypto_terms:
            assert bad_term not in full_text, (
                f"Found Crypto term '{bad_term}' in OS quiz question: {q['question']}"
            )


def test_quiz_generation_invalid_document_returns_404():
    """Verify that requesting a quiz with a non-existent document ID returns a clean 404 error."""
    payload = {
        "document_id": "non-existent-uuid-12345",
        "topic": "General",
        "difficulty": "medium",
        "question_count": 3
    }
    res = client.post("/api/quiz/generate", json=payload)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_repeated_cross_document_isolation(setup_two_documents):
    """
    Verify that alternating quiz generation across documents (Doc A -> Doc B -> Doc A)
    never carries over stale state, cached questions, or cross-document topics.
    """
    data = setup_two_documents
    crypto_id = data["crypto_id"]
    os_id = data["os_id"]

    # 1. Generate for Data Security
    res1 = client.post("/api/quiz/generate", json={
        "document_id": crypto_id,
        "topic": "Classical Encryption Techniques",
        "question_count": 3
    })
    assert res1.status_code == 201
    q1 = res1.json()
    assert all("deadlock" not in q["question"].lower() for q in q1["questions"])

    # 2. Generate for Operating Systems
    res2 = client.post("/api/quiz/generate", json={
        "document_id": os_id,
        "topic": "Process Synchronization",
        "question_count": 3
    })
    assert res2.status_code == 201
    q2 = res2.json()
    assert all("cipher" not in q["question"].lower() for q in q2["questions"])

    # 3. Generate NEW quiz for Data Security again - must remain 100% security content
    res3 = client.post("/api/quiz/generate", json={
        "document_id": crypto_id,
        "topic": "Classical Encryption Techniques",
        "question_count": 3
    })
    assert res3.status_code == 201
    q3 = res3.json()
    assert all("deadlock" not in q["question"].lower() for q in q3["questions"])
    assert all("banker" not in q["question"].lower() for q in q3["questions"])
    assert all("ostrich" not in q["question"].lower() for q in q3["questions"])
    assert all("Operating_Systems" not in q.get("citation", "") for q in q3["questions"])

