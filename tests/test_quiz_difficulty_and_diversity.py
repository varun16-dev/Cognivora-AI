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
from app.agents.quiz_agent import QuizAgent, HARD_ANALYTICAL_INDICATORS, TRIVIAL_DEFINITION_PREFIXES

client = TestClient(app)

CAESAR_CIPHER_TEXT = """## Subject: Cryptography and Network Security
### Chapter: Classical Substitution Ciphers

The Caesar cipher is one of the earliest and simplest known encryption techniques.
It is a type of substitution cipher in which each letter in the plaintext is replaced by a letter some fixed number of positions down the alphabet.
For example, with a left shift of 3, D would be replaced by A, E would become B, and so on.
The method is named after Julius Caesar, who used it in his private correspondence.

Mathematical Formulation:
The encryption of a letter x by a shift n can be described mathematically as:
E_n(x) = (x + n) mod 26
Decryption of a ciphertext letter y is performed using:
D_n(y) = (y - n) mod 26

Cryptanalysis and Weaknesses:
The Caesar cipher provides virtually no communication security in modern systems.
Because the English alphabet contains only 26 letters, there are only 25 possible keys (excluding key 0 which performs no transformation).
An attacker can easily perform a brute-force attack by testing all 25 shift values until intelligible plaintext appears.
Furthermore, because each letter always maps to the same corresponding letter, monoalphabetic substitution does not alter the underlying letter frequency distribution of the language.
An adversary with sufficient ciphertext can easily break the cipher using frequency analysis.
"""

RNN_DEEP_LEARNING_TEXT = """## Subject: Deep Learning and Natural Language Processing
### Chapter: Recurrent Neural Networks and Sequence Modeling

Recurrent Neural Networks (RNNs) are a class of artificial neural networks designed for processing sequential data.
Unlike traditional feedforward neural networks that assume all inputs and outputs are independent, RNNs utilize internal memory to process variable-length sequences of inputs.
At each time step t, an RNN computes a hidden state h_t based on the current input x_t and the previous hidden state h_{t-1}:
h_t = tanh(W_hh * h_{t-1} + W_xh * x_t + b_h)

The Vanishing and Exploding Gradient Problem:
Standard RNNs suffer significantly from the vanishing gradient problem during backpropagation through time (BPTT).
When computing gradients across long temporal sequences, repeated multiplication of weight matrices causes exponential decay or explosion of gradients.
To address this limitation, Long Short-Term Memory (LSTM) networks introduce gated memory cells with input, forget, and output gates.
Gated Recurrent Units (GRUs) offer a computationally efficient alternative by merging the cell state and hidden state using reset and update gates.
"""


@pytest.fixture(scope="module")
def setup_test_documents(tmp_path_factory):
    """Indexes Caesar Cipher and RNN documents for testing."""
    init_db()
    db = SessionLocal()

    temp_dir = tmp_path_factory.mktemp("quiz_eval_docs")

    # Document 1: Caesar Cipher
    caesar_file = temp_dir / "Caesar_Cipher_Notes.txt"
    caesar_file.write_text(CAESAR_CIPHER_TEXT, encoding="utf-8")
    doc_caesar = DocumentAgent.process_and_index_document(
        file_path=str(caesar_file),
        original_filename="Caesar_Cipher_Notes.txt",
        db=db
    )

    # Document 2: RNN Deep Learning
    rnn_file = temp_dir / "RNN_Sequence_Modeling.txt"
    rnn_file.write_text(RNN_DEEP_LEARNING_TEXT, encoding="utf-8")
    doc_rnn = DocumentAgent.process_and_index_document(
        file_path=str(rnn_file),
        original_filename="RNN_Sequence_Modeling.txt",
        db=db
    )

    caesar_id = doc_caesar.id
    rnn_id = doc_rnn.id
    db.close()

    yield {
        "caesar_id": caesar_id,
        "caesar_name": "Caesar_Cipher_Notes.txt",
        "rnn_id": rnn_id,
        "rnn_name": "RNN_Sequence_Modeling.txt"
    }


def test_caesar_cipher_easy_difficulty(setup_test_documents):
    """Verify EASY quiz generates accessible recall, definition, and basic questions."""
    caesar_id = setup_test_documents["caesar_id"]
    res = client.post("/api/quiz/generate", json={
        "document_id": caesar_id,
        "topic": "Classical Substitution Ciphers",
        "difficulty": "easy",
        "question_count": 3,
        "question_types": ["mcq", "true_false"]
    })
    assert res.status_code == 201
    quiz = res.json()
    assert quiz["difficulty"] == "easy"
    assert len(quiz["questions"]) == 3

    for q in quiz["questions"]:
        assert q["options"] and len(q["options"]) >= 2
        assert q["correct_answer"] in q["options"]
        assert "Caesar_Cipher_Notes.txt" in q["citation"]
        # Must reflect Caesar cipher concepts
        full_text = f"{q['question']} {' '.join(q['options'])}".lower()
        assert any(k in full_text for k in ["caesar", "cipher", "substitution", "letter", "shift", "alphabet", "julius"])


def test_caesar_cipher_medium_difficulty(setup_test_documents):
    """Verify MEDIUM quiz focuses on application, calculation, mechanisms, and comparisons."""
    caesar_id = setup_test_documents["caesar_id"]
    res = client.post("/api/quiz/generate", json={
        "document_id": caesar_id,
        "topic": "Classical Substitution Ciphers",
        "difficulty": "medium",
        "question_count": 3,
        "question_types": ["mcq"]
    })
    assert res.status_code == 201
    quiz = res.json()
    assert quiz["difficulty"] == "medium"
    assert len(quiz["questions"]) == 3

    for q in quiz["questions"]:
        assert len(q["options"]) == 4
        assert q["correct_answer"] in q["options"]
        assert not q["question"].lower().startswith("what is the definition of")
        assert "Caesar_Cipher_Notes.txt" in q["citation"]


def test_caesar_cipher_hard_difficulty_strict_analytic(setup_test_documents):
    """
    Verify HARD quiz requires multi-step analytical reasoning or scenario analysis.
    STRICTLY NO True/False questions, NO basic definitions, and NO trivial recall.
    """
    caesar_id = setup_test_documents["caesar_id"]
    res = client.post("/api/quiz/generate", json={
        "document_id": caesar_id,
        "topic": "Classical Substitution Ciphers",
        "difficulty": "hard",
        "question_count": 3,
        "question_types": ["mcq", "true_false"]  # Should enforce MCQs regardless
    })
    assert res.status_code == 201
    quiz = res.json()
    assert quiz["difficulty"] == "hard"
    assert len(quiz["questions"]) == 3

    for q in quiz["questions"]:
        # Hard questions must be 4-option MCQs (NO True/False)
        assert q["question_type"] == "mcq", "Hard questions must not be True/False"
        assert len(q["options"]) == 4
        assert q["correct_answer"] in q["options"]

        prompt = q["question"].strip().lower()

        # Hard questions must not be simple definitions
        for prefix in TRIVIAL_DEFINITION_PREFIXES:
            if prompt.startswith(prefix):
                assert "scenario" in prompt or "suppose" in prompt, f"Hard question starts with trivial definition: {prompt}"

        # Hard questions must feature cognitive complexity or analytical markers
        has_analytical = any(ind in prompt for ind in HARD_ANALYTICAL_INDICATORS)
        is_substantial = len(prompt) >= 70
        assert has_analytical or is_substantial, f"Question lacks hard analytical complexity: {prompt}"
        assert "Caesar_Cipher_Notes.txt" in q["citation"]


def test_rnn_deep_learning_document_isolation(setup_test_documents):
    """Verify RNN Deep Learning quiz is strictly isolated from Caesar cipher."""
    rnn_id = setup_test_documents["rnn_id"]
    res = client.post("/api/quiz/generate", json={
        "document_id": rnn_id,
        "topic": "Recurrent Neural Networks",
        "difficulty": "medium",
        "question_count": 3
    })
    assert res.status_code == 201
    quiz = res.json()
    assert quiz["document_id"] == rnn_id

    forbidden_crypto = ["caesar", "cipher", "plaintext", "ciphertext", "substitution"]
    required_rnn = ["rnn", "gradient", "hidden state", "lstm", "gru", "sequential", "sequence", "network"]

    found_rnn_concept = False
    for q in quiz["questions"]:
        full_text = f"{q['question']} {' '.join(q['options'])}".lower()
        for bad in forbidden_crypto:
            assert bad not in full_text, f"Crypto concept '{bad}' leaked into RNN quiz!"
        if any(r in full_text for r in required_rnn):
            found_rnn_concept = True
        assert "RNN_Sequence_Modeling.txt" in q["citation"]

    assert found_rnn_concept, "RNN quiz must test sequential deep learning concepts"


def test_duplicate_prevention_across_consecutive_quizzes(setup_test_documents):
    """
    Verify consecutive quiz generations on the same document and topic
    do not return identical questions.
    """
    caesar_id = setup_test_documents["caesar_id"]

    # 1. First quiz generation
    res1 = client.post("/api/quiz/generate", json={
        "document_id": caesar_id,
        "topic": "Classical Substitution Ciphers",
        "difficulty": "medium",
        "question_count": 3
    })
    assert res1.status_code == 201
    q_set_1 = [q["question"].strip() for q in res1.json()["questions"]]

    # 2. Second quiz generation on identical topic & difficulty
    res2 = client.post("/api/quiz/generate", json={
        "document_id": caesar_id,
        "topic": "Classical Substitution Ciphers",
        "difficulty": "medium",
        "question_count": 3
    })
    assert res2.status_code == 201
    q_set_2 = [q["question"].strip() for q in res2.json()["questions"]]

    # Verify no identical prompt was duplicated
    for prompt2 in q_set_2:
        for prompt1 in q_set_1:
            similarity = QuizAgent._calculate_jaccard_similarity(prompt1, prompt2)
            assert similarity < 0.90, f"Identical or near-duplicate question returned: '{prompt2}' vs '{prompt1}' (similarity={similarity:.2f})"


def test_internal_quiz_deduplication(setup_test_documents):
    """Verify that within a single generated quiz, all questions are mutually distinct."""
    caesar_id = setup_test_documents["caesar_id"]
    res = client.post("/api/quiz/generate", json={
        "document_id": caesar_id,
        "topic": "Classical Substitution Ciphers",
        "difficulty": "hard",
        "question_count": 5
    })
    assert res.status_code == 201
    questions = res.json()["questions"]
    prompts = [q["question"].strip() for q in questions]

    for i in range(len(prompts)):
        for j in range(i + 1, len(prompts)):
            sim = QuizAgent._calculate_jaccard_similarity(prompts[i], prompts[j])
            assert sim < 0.70, f"Questions {i} and {j} within same quiz are too similar: {prompts[i]} vs {prompts[j]}"


def test_correct_answer_and_options_integrity(setup_test_documents):
    """Verify every question has valid, distinct options and exactly one matching correct answer."""
    caesar_id = setup_test_documents["caesar_id"]
    res = client.post("/api/quiz/generate", json={
        "document_id": caesar_id,
        "topic": "Classical Substitution Ciphers",
        "difficulty": "easy",
        "question_count": 4,
        "question_types": ["mcq"]
    })
    assert res.status_code == 201
    for q in res.json()["questions"]:
        options = q["options"]
        assert len(options) == len(set(options)), f"Options contain duplicates: {options}"
        assert q["correct_answer"] in options, f"Correct answer '{q['correct_answer']}' not found in options {options}"


def test_insufficient_or_invalid_document_content():
    """Verify clean 404 or 400 when document ID does not exist."""
    res = client.post("/api/quiz/generate", json={
        "document_id": "non-existent-doc-uuid-9999",
        "topic": "Cryptography",
        "difficulty": "medium",
        "question_count": 3
    })
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
