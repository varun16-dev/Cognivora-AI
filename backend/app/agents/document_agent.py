import os
import json
import uuid
import logging
from typing import List, Dict, Any, Tuple,Optional
from sqlalchemy.orm import Session
from app.services.document_parser import DocumentParser
from app.services.rag_engine import rag_engine
from app.database.models import DocumentModel

logger = logging.getLogger("CognivoraAI.DocumentAgent")


class DocumentAgent:
    """
    Specialized Agent for Document Ingestion, Semantic Chunking,
    Vector Indexing, and Grounded Retrieval.
    """

    @staticmethod
    def process_and_index_document(
        file_path: str,
        original_filename: str,
        db: Session
    ) -> DocumentModel:
        """
        Parses document, extracts topic hierarchy, chunks text,
        and indexes chunks in ChromaDB.
        """
        doc_id = str(uuid.uuid4())
        file_size = os.path.getsize(file_path)
        ext = os.path.splitext(original_filename)[1].lower()

        logger.info(f"[DocumentAgent] Processing '{original_filename}' ({file_size} bytes)")

        try:
            # 1. Extract pages
            pages = DocumentParser.extract_text_from_file(file_path)

            # 2. Extract topics & subject
            subject, topics = DocumentParser.extract_topics_and_subject(pages)

            # 3. Semantic chunking
            chunks = DocumentParser.semantic_chunk_pages(pages)

            # 4. Index in vector store
            indexed_count = rag_engine.index_document_chunks(
                document_id=doc_id,
                document_name=original_filename,
                subject=subject,
                chunks=chunks
            )

            # 5. Persist Document record
            doc_record = DocumentModel(
                id=doc_id,
                filename=original_filename,
                file_type=ext.replace(".", ""),
                file_size_bytes=file_size,
                subject=subject,
                chunk_count=indexed_count,
                topics_json=json.dumps(topics),
                summary=f"Processed academic document containing {len(pages)} pages and {indexed_count} indexed chunks.",
                processing_status="processed"
            )
            db.add(doc_record)
            db.commit()
            db.refresh(doc_record)

            logger.info(f"[DocumentAgent] Successfully indexed '{original_filename}' with {indexed_count} chunks.")
            return doc_record

        except Exception as e:
            logger.error(f"[DocumentAgent] Document processing failed: {e}")
            error_doc = DocumentModel(
                id=doc_id,
                filename=original_filename,
                file_type=ext.replace(".", ""),
                file_size_bytes=file_size,
                subject="Unknown",
                chunk_count=0,
                topics_json="[]",
                summary="Processing failed.",
                processing_status="error",
                error_message=str(e)
            )
            db.add(error_doc)
            db.commit()
            raise RuntimeError(f"DocumentAgent failed: {str(e)}")

    @staticmethod
    def retrieve_grounded_context(
        query: str,
        document_id: str = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Retrieves context chunks strictly relevant to query.
        """
        return rag_engine.retrieve_relevant_chunks(
            query=query,
            document_id=document_id,
            top_k=top_k
        )
