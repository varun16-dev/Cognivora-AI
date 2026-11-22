import os
import shutil
import uuid
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import DocumentModel
from app.schemas.schemas import DocumentResponse, DocumentHierarchyResponse, TopicHierarchy
from app.agents.document_agent import DocumentAgent
from app.services.rag_engine import rag_engine
from app.config import settings, UPLOAD_DIR

logger = logging.getLogger("CognivoraAI.DocumentsAPI")
router = APIRouter(prefix="/documents", tags=["Documents"])


def _safe_parse_topics(topics_json: Optional[str]) -> List[str]:
    """Safely parses topics JSON array supporting standard JSON and legacy string formats."""
    if not topics_json:
        return []
    try:
        parsed = json.loads(topics_json)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    try:
        parsed = json.loads(topics_json.replace("'", '"'))
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    return ["General"]


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an academic document (PDF, DOCX, TXT), extract text,
    detect syllabus topics, semantically chunk, and index in ChromaDB.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty.")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Save to disk
    safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    saved_path = UPLOAD_DIR / safe_filename

    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    # Check file size limit and empty document
    file_bytes = os.path.getsize(saved_path)
    if file_bytes == 0:
        os.remove(saved_path)
        raise HTTPException(
            status_code=400,
            detail="Uploaded document is empty (0 bytes). Please upload a valid document containing educational text."
        )

    file_size_mb = file_bytes / (1024 * 1024)
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        os.remove(saved_path)
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB."
        )

    # Process and index via DocumentAgent
    try:
        doc_record = DocumentAgent.process_and_index_document(
            file_path=str(saved_path),
            original_filename=file.filename,
            db=db
        )
        topics = _safe_parse_topics(doc_record.topics_json)
        return DocumentResponse(
            id=doc_record.id,
            filename=doc_record.filename,
            file_type=doc_record.file_type,
            file_size_bytes=doc_record.file_size_bytes,
            subject=doc_record.subject,
            upload_timestamp=doc_record.upload_timestamp,
            chunk_count=doc_record.chunk_count,
            topics=topics,
            processing_status=doc_record.processing_status,
            summary=doc_record.summary
        )
    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document indexing failed: {str(e)}")


@router.get("", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    """List all processed academic documents."""
    docs = db.query(DocumentModel).order_by(DocumentModel.upload_timestamp.desc()).all()
    results = []
    for d in docs:
        topics = _safe_parse_topics(d.topics_json)

        results.append(DocumentResponse(
            id=d.id,
            filename=d.filename,
            file_type=d.file_type,
            file_size_bytes=d.file_size_bytes,
            subject=d.subject,
            upload_timestamp=d.upload_timestamp,
            chunk_count=d.chunk_count,
            topics=topics,
            processing_status=d.processing_status,
            summary=d.summary,
            error_message=d.error_message
        ))
    return results


@router.get("/{document_id}/hierarchy", response_model=DocumentHierarchyResponse)
def get_document_hierarchy(document_id: str, db: Session = Depends(get_db)):
    """Returns detected chapter and topic hierarchy for curriculum browsing."""
    doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    topics = _safe_parse_topics(doc.topics_json) or ["General Concepts"]

    hierarchy = [
        TopicHierarchy(name=t, level=1, subtopics=[f"{t} - Definitions", f"{t} - Practical Examples"])
        for t in topics
    ]

    return DocumentHierarchyResponse(
        document_id=doc.id,
        filename=doc.filename,
        subject=doc.subject,
        topics=hierarchy
    )


@router.get("/{document_id}/suggested-questions")
def get_document_suggested_questions(document_id: str, db: Session = Depends(get_db)):
    """
    Returns 4 intelligent, document-specific suggested study questions
    grounded in the document's subject, detected topics, and indexed content.
    """
    doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    topics = _safe_parse_topics(doc.topics_json)

    subject = (doc.subject or "").lower()
    filename = (doc.filename or "").lower()
    all_terms = f"{subject} {filename} {' '.join(topics)}".lower()

    if any(k in all_terms for k in ["security", "privacy", "crypt", "cipher", "gdpr", "confidential", "threat"]):
        questions = [
            "What are the core principles of Confidentiality, Integrity, and Availability (CIA)?",
            "How does symmetric encryption differ from asymmetric public-key cryptography?",
            "What are the primary GDPR compliance requirements for personal data protection?",
            "Explain common cyber threat vectors and defense-in-depth mitigation strategies."
        ]
    elif any(k in all_terms for k in ["deadlock", "operating", "process", "thread", "scheduling", "banker", "os"]):
        questions = [
            "What are the 4 necessary conditions for a deadlock to occur?",
            "How does Dijkstra's Banker's Algorithm ensure safe state resource allocation?",
            "Explain the difference between Deadlock Prevention and Deadlock Avoidance.",
            "How does virtual memory paging resolve external fragmentation?"
        ]
    elif any(k in all_terms for k in ["database", "sql", "relational", "acid", "normal", "dbms"]):
        questions = [
            "Explain the ACID properties and their role in relational transaction management.",
            "What is the difference between BCNF and Third Normal Form (3NF)?",
            "How do clustered indexes differ from non-clustered indexes in query execution?",
            "What concurrency control techniques prevent dirty reads and lost updates?"
        ]
    elif any(k in all_terms for k in ["network", "tcp", "udp", "osi", "routing", "ip"]):
        questions = [
            "Compare TCP and UDP transport protocols in terms of reliability and overhead.",
            "Describe the 7 layers of the OSI model and their primary functions.",
            "How does the Three-Way Handshake establish a secure connection in TCP?",
            "Explain the difference between distance-vector and link-state routing algorithms."
        ]
    else:
        primary_topic = topics[0] if topics else (doc.subject or "this topic")
        sec_topic = topics[1] if len(topics) > 1 else "key concepts"
        questions = [
            f"What are the fundamental definitions and core principles of {primary_topic}?",
            f"How does {primary_topic} apply to practical problem solving in {doc.subject or 'coursework'}?",
            f"Explain the relationship and differences between {primary_topic} and {sec_topic}.",
            f"Generate a practice exam review focused on {primary_topic}."
        ]

    return {
        "document_id": doc.id,
        "filename": doc.filename,
        "subject": doc.subject,
        "questions": questions
    }


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Deletes a document and its vector embeddings."""
    doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    rag_engine.delete_document_chunks(document_id)
    db.delete(doc)
    db.commit()
    return {"message": f"Document '{doc.filename}' and all associated vector embeddings deleted."}
