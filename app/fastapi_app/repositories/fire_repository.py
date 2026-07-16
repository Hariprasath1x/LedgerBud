"""FIRE repository — persistence layer for FireAnalysis records."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.fastapi_app.models.fire import FireAnalysis


class FireRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, analysis: FireAnalysis) -> FireAnalysis:
        """Persist a FireAnalysis record and return refreshed instance."""
        self.session.add(analysis)
        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def get_latest(self, user_id: int) -> FireAnalysis | None:
        """Return the most recent analysis for this user."""
        return self.session.scalar(
            select(FireAnalysis)
            .where(FireAnalysis.user_id == user_id)
            .order_by(FireAnalysis.created_at.desc())
            .limit(1)
        )

    def list_history(self, user_id: int, limit: int = 20) -> list[FireAnalysis]:
        """Return paginated history of FIRE analyses, newest first."""
        return list(
            self.session.scalars(
                select(FireAnalysis)
                .where(FireAnalysis.user_id == user_id)
                .order_by(FireAnalysis.created_at.desc())
                .limit(limit)
            ).all()
        )
