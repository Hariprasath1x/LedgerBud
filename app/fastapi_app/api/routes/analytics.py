"""Analytics routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.schemas.analytics import (
    AnalyticsSummary,
    CategoryBreakdown,
    MerchantPoint,
    TrendPoint,
    WhatIfRequest,
    WhatIfResponse,
)
from app.fastapi_app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return AnalyticsService(session).get_summary(current_user.id)


@router.get("/trends", response_model=list[TrendPoint])
def get_trends(
    months: int = 6,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return AnalyticsService(session).get_trends(current_user.id, months=months)


@router.get("/categories", response_model=list[CategoryBreakdown])
def get_categories(
    year: int | None = None,
    month: int | None = None,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return AnalyticsService(session).get_category_breakdown(current_user.id, year=year, month=month)


@router.get("/merchants", response_model=list[MerchantPoint])
def get_merchants(
    limit: int = 10,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return AnalyticsService(session).get_top_merchants(current_user.id, limit=limit)


@router.post("/whatif", response_model=WhatIfResponse)
def run_whatif_simulation(
    payload: WhatIfRequest,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return AnalyticsService(session).whatif_simulation(current_user.id, payload)
