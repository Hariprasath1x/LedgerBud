"""Goal service — CRUD and contribution management."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.fastapi_app.models.goal import Goal
from app.fastapi_app.schemas.goal import GoalContribute, GoalCreate, GoalUpdate


class GoalService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_goals(self, user_id: int) -> list[Goal]:
        return list(
            self.session.scalars(
                select(Goal).where(Goal.user_id == user_id).order_by(Goal.status, Goal.target_date)
            ).all()
        )

    def get_goal(self, user_id: int, goal_id: int) -> Goal | None:
        return self.session.scalar(select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id))

    def create_goal(self, user_id: int, payload: GoalCreate) -> Goal:
        goal = Goal(
            user_id=user_id,
            name=payload.name,
            description=payload.description,
            target_amount=payload.target_amount,
            current_amount=payload.current_amount,
            target_date=payload.target_date,
            status="active",
        )
        self.session.add(goal)
        self.session.commit()
        self.session.refresh(goal)
        return goal

    def update_goal(self, user_id: int, goal_id: int, payload: GoalUpdate) -> Goal | None:
        goal = self.get_goal(user_id, goal_id)
        if not goal:
            return None
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(goal, field, value)
        self.session.commit()
        self.session.refresh(goal)
        return goal

    def contribute(self, user_id: int, goal_id: int, payload: GoalContribute) -> Goal | None:
        goal = self.get_goal(user_id, goal_id)
        if not goal:
            return None
        goal.current_amount = float(goal.current_amount) + payload.amount
        if float(goal.current_amount) >= float(goal.target_amount):
            goal.status = "completed"
        self.session.commit()
        self.session.refresh(goal)
        return goal

    def delete_goal(self, user_id: int, goal_id: int) -> bool:
        goal = self.get_goal(user_id, goal_id)
        if not goal:
            return False
        self.session.delete(goal)
        self.session.commit()
        return True
