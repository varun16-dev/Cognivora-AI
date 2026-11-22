import os
import shutil
import uuid
import json
import logging
from typing import List
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
        topics = json.loads(doc_record.topics_json.replace("'", '"')) if doc_record.topics_json else []
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
        try:
            topics = json.loads(d.topics_json.replace("'", '"')) if d.topics_json else []
        except Exception:
            topics = ["General"]

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

    try:
        topics = json.loads(doc.topics_json.replace("'", '"')) if doc.topics_json else []
    except Exception:
        topics = ["General Concepts"]

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
