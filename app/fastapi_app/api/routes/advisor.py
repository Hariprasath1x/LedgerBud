"""Advisor endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_current_user, get_session
from app.fastapi_app.schemas.advisor import AdvisorRequest, AdvisorResponse
from app.fastapi_app.services.advisor_service import AdvisorService

router = APIRouter(prefix="/advisor", tags=["Advisor"])


@router.post("/ask", response_model=AdvisorResponse)
def ask_advisor(payload: AdvisorRequest, current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    return AdvisorService(session).ask_advisor(current_user.id, payload)


@router.get("/context")
def get_advisor_context(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
    """Fetch the context payload that will be sent to the LLM (for debugging/transparency)."""
    return AdvisorService(session).get_context_summary(current_user.id)
