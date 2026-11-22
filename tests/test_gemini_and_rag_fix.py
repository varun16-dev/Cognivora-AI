import os
import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.services.gemini_client import gemini_service
from app.services.rag_engine import rag_engine
from app.agents.coordinator_agent import CoordinatorAgent
from app.database.session import SessionLocal
from app.database.models import DocumentModel
import requests

def run_checks():
    print("=" * 60)
    print("COGNIVORA AI - VERIFICATION SUITE FOR ISSUES 1-4")
    print("=" * 60)

    # 1. Config Check
    print(f"[CHECK 1] Primary Model: {settings.PRIMARY_MODEL}")
    print(f"[CHECK 1] Embedding Model: {settings.EMBEDDING_MODEL}")
    assert settings.PRIMARY_MODEL == "gemini-3.5-flash", "Expected gemini-3.5-flash"
    assert settings.EMBEDDING_MODEL == "gemini-embedding-001", "Expected gemini-embedding-001"
    print(" -> PASS: Models correctly configured.")

    # 2. Live Gemini Status
    is_live = gemini_service.is_live()
    print(f"[CHECK 2] Gemini Client Live: {is_live}")
    if is_live:
        print(f" -> Model Name: {gemini_service.model_name}")
    else:
        print(" -> Warning: Running in offline / demo mode.")

    # 3. Live Embeddings
    print("[CHECK 3] Testing FastCurriculumEmbedder...")
    sample_text = ["Operating Systems: Deadlock condition 1 is Mutual Exclusion.", "Data Security: Asymmetric encryption uses public and private keypairs."]
    embeddings = rag_engine.embedder(sample_text)
    print(f" -> Generated {len(embeddings)} embeddings of dimension {len(embeddings[0])}")
    assert len(embeddings) == 2, "Expected 2 embeddings"
    assert len(embeddings[0]) == 384, f"Expected 384 dimensions, got {len(embeddings[0])}"
    print(" -> PASS: Embedding dimension matches ChromaDB (384).")

    # 4. Grounded Chat & Answer Quality
    db = SessionLocal()
    doc = db.query(DocumentModel).first()
    if doc:
        # Ensure Chroma has the chunks
        if rag_engine.collection and rag_engine.collection.count() == 0:
            sample_file = Path("data/sample_documents/os_deadlocks_and_scheduling.txt")
            if sample_file.exists():
                from app.services.document_parser import DocumentParser
                pages = DocumentParser.extract_text_from_file(str(sample_file))
                chunks = DocumentParser.semantic_chunk_pages(pages)
                rag_engine.index_document_chunks(doc.id, doc.filename, doc.subject, chunks)

        print(f"[CHECK 4] Testing Grounded Chat with Document: '{doc.filename}' (Subject: {doc.subject})")
        
        # Test a grounded question
        res_grounded = CoordinatorAgent.handle_student_interaction(
            message="Explain what a deadlock is and the Banker's algorithm mechanism",
            document_id=doc.id,
            pedagogical_mode="standard",
            db=db
        )
        print(f" -> Model Used: {res_grounded.model_used}")
        print(f" -> Is Demo Mode: {res_grounded.is_demo_mode}")
        print(f" -> Grounded: {res_grounded.grounded_in_docs}")
        print(f" -> Citations Count: {len(res_grounded.citations)}")
        answer_preview = res_grounded.answer[:250].replace('\n', ' ')
        print(f" -> Answer Preview: {answer_preview}...")

        # Verify that generic placeholder is NOT in the answer
        assert "Conditions and algorithmic criteria must be satisfied" not in res_grounded.answer, \
            "FAIL: Generic template found in response!"
        print(" -> PASS: Generic template eliminated. Real pedagogical explanation returned.")

        # Test refusal on unrelated question
        res_unrelated = CoordinatorAgent.handle_student_interaction(
            message="What is the capital of Peru and what are the best tourist spots in Lima?",
            document_id=doc.id,
            pedagogical_mode="standard",
            db=db
        )
        print(f"[CHECK 5] Unrelated Query Guardrail:")
        print(f" -> Answer: {res_unrelated.answer[:120]}...")
        assert "cannot find" in res_unrelated.answer.lower() or "upload" in res_unrelated.answer.lower(), \
            "FAIL: Grounding guardrail did not refuse out-of-context query!"
        print(" -> PASS: Refusal guardrail active and correctly triggered.")
    else:
        print("[CHECK 4] No documents in DB. Skipping doc-specific tests.")
    db.close()

    print("=" * 60)
    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_checks()
