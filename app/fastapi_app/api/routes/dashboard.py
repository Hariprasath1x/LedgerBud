"""Dashboard and intelligence routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.schemas.dashboard import DashboardResponse
from app.fastapi_app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    return DashboardService(session).dashboard_payload(current_user.id)


@router.get("/health-score")
def get_health_score(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    return DashboardService(session).calculate_health_score(current_user.id)


@router.get("/insights")
def get_insights(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    return DashboardService(session).generate_insights(current_user.id)
