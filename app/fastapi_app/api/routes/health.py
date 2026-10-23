"""Health check endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.fastapi_app.api.deps import get_session

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check(session: Session = Depends(get_session)) -> dict[str, str]:
    """Readiness probe verifying application and database connectivity."""
    try:
        session.execute(text("SELECT 1"))
        return {"status": "ok", "service": "LedgerBud API", "database": "connected"}
    except Exception as exc:
        logger.error("Health check database probe failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        ) from None


@router.get("/health/live")
def liveness_check() -> dict[str, str]:
    """Lightweight liveness probe verifying process responsiveness."""
    return {"status": "ok", "service": "LedgerBud API"}
