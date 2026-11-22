from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.schemas import AnalyticsDashboardResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
def get_dashboard_analytics(db: Session = Depends(get_db)):
    """
    Returns student learning metrics: average scores, EWMA topic mastery heatmaps,
    weak areas identification (<60%), and personalized revision alerts.
    """
    return AnalyticsService.get_dashboard_metrics(db)
