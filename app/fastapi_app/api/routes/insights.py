"""Insights endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.schemas.dashboard import InsightItem
from app.fastapi_app.services.insights_service import InsightsService

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("", response_model=list[InsightItem])
def get_insights(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    return InsightsService(session).generate_insights(current_user.id)
