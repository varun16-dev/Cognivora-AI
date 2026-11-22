import os
import sys
import shutil
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Bootstrap backend directory into sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings, SAMPLE_DIR
from app.database.session import init_db, SessionLocal
from app.database.models import DocumentModel
from app.agents.document_agent import DocumentAgent
from app.api.documents import router as documents_router
from app.api.agent import router as agent_router
from app.api.quiz import router as quiz_router
from app.api.flashcards import router as flashcards_router
from app.api.summary import router as summary_router
from app.api.analytics import router as analytics_router
from app.api.health import router as health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("CognivoraAI")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown events."""
    logger.info("Initializing Cognivora AI backend services...")
    # 1. Initialize SQLite Database Tables
    init_db()

    # 2. Check if default sample document is loaded and indexed; if not, auto-seed/sync
    db = SessionLocal()
    try:
        from app.services.rag_engine import rag_engine
        from app.agents.document_agent import TextExtractor
        
        doc_count = db.query(DocumentModel).count()
        chroma_empty = (rag_engine.collection is not None and rag_engine.collection.count() == 0)

        if doc_count == 0:
            sample_file = SAMPLE_DIR / "os_deadlocks_and_scheduling.txt"
            if sample_file.exists():
                logger.info(f"Seeding default sample academic document from '{sample_file}'...")
                DocumentAgent.process_and_index_document(
                    file_path=str(sample_file),
                    original_filename="Operating_Systems_Unit3_Deadlocks.txt",
                    db=db
                )
        elif chroma_empty:
            # Re-index existing sample docs into ChromaDB
            sample_file = SAMPLE_DIR / "os_deadlocks_and_scheduling.txt"
            if sample_file.exists():
                existing_doc = db.query(DocumentModel).filter(
                    DocumentModel.filename == "Operating_Systems_Unit3_Deadlocks.txt"
                ).first()
                if existing_doc:
                    logger.info("Re-indexing existing sample document chunks into ChromaDB...")
                    from app.services.document_parser import DocumentParser
                    pages = DocumentParser.extract_text_from_file(str(sample_file))
                    chunks = DocumentParser.semantic_chunk_pages(pages)
                    rag_engine.index_document_chunks(existing_doc.id, existing_doc.filename, existing_doc.subject, chunks)
    except Exception as e:
        logger.warning(f"Initial sample document seeding/sync skipped: {e}")
    finally:
        db.close()

    logger.info("Cognivora AI backend initialized and ready.")
    yield
    logger.info("Cognivora AI backend shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-Agent AI Educational Assistant for Grounded Q&A, Quizzes, Flashcards, Summaries & Analytics",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api/v1 and /api
app.include_router(health_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(quiz_router, prefix="/api")
app.include_router(flashcards_router, prefix="/api")
app.include_router(summary_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "documentation": "/docs",
        "health_check": "/api/health"
    }
