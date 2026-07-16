"""FIRE Intelligence Engine API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.schemas.fire import (
    FireAIRequest,
    FireAIResponse,
    FireCalculationResult,
    FireDashboardResponse,
    FireHistoryItem,
    FireSettings,
)
from app.fastapi_app.services.fire_service import FIREService
from app.fastapi_app.services.advisor_service import AdvisorService
from app.fastapi_app.schemas.advisor import AdvisorResponse

router = APIRouter(prefix="/fire", tags=["FIRE Intelligence"])


@router.get("", response_model=FireDashboardResponse)
def get_fire_dashboard(
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Return the latest stored FIRE dashboard. Returns has_data=False if no calculation exists yet."""
    return FIREService(session).get_dashboard(current_user.id)


@router.post("/calculate", response_model=FireCalculationResult)
def calculate_fire(
    settings: FireSettings,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Run the full 10-step FIRE calculation engine.
    Auto-fetches income, expenses, net worth, budgets, goals and subscriptions.
    Stores the result in fire_analysis for historical tracking.
    """
    return FIREService(session).calculate(current_user.id, settings)


@router.get("/history", response_model=list[FireHistoryItem])
def get_fire_history(
    limit: int = 20,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Return paginated history of FIRE analyses for this user."""
    return FIREService(session).get_history(current_user.id, limit=limit)


@router.post("/ai", response_model=AdvisorResponse)
def ask_fire_coach(
    payload: FireAIRequest,
    current_user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Ask the FIRE Coach — uses existing Groq AI advisor with FIRE-enriched context.
    Pass optional fire_context to avoid double-fetching if already loaded on the client.
    """
    fire_svc = FIREService(session)
    advisor_svc = AdvisorService(session)

    # Use provided context or build from DB
    fire_context = payload.fire_context or fire_svc.build_fire_context(current_user.id)

    return advisor_svc.ask_fire_advisor(
        user_id=current_user.id,
        question=payload.question,
        fire_context=fire_context,
        history=payload.history,
    )
