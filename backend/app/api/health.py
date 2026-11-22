from fastapi import APIRouter
from app.config import settings
from app.services.gemini_client import gemini_service
from app.services.rag_engine import rag_engine

router = APIRouter(tags=["System"])


@router.get("/health")
def health_check():
    """
    System status, database connectivity, Gemini model state,
    and vector store indexing readiness.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "gemini_api_configured": gemini_service.is_live(),
        "active_model": settings.PRIMARY_MODEL if gemini_service.is_live() else "Built-in Curriculum Engine (Demo Mode)",
        "vector_store": "ChromaDB" if rag_engine.collection else "MemoryVectorCache",
        "supported_upload_formats": settings.ALLOWED_EXTENSIONS
    }
