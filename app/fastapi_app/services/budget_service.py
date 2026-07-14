"""Budget service — CRUD and usage calculation."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.fastapi_app.models.budget import Budget
from app.fastapi_app.models.transaction import Transaction
from app.fastapi_app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetWithUsage


class BudgetService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_budgets(self, user_id: int) -> list[BudgetWithUsage]:
        budgets = self.session.scalars(
            select(Budget).where(Budget.user_id == user_id, Budget.is_active == True).order_by(Budget.name)
        ).all()
        return [self._enrich(b) for b in budgets]

    def get_budget(self, user_id: int, budget_id: int) -> Budget | None:
        return self.session.scalar(
            select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
        )

    def create_budget(self, user_id: int, payload: BudgetCreate) -> Budget:
        today = date.today()
        budget = Budget(
            user_id=user_id,
            name=payload.name,
            category=payload.category,
            amount=payload.amount,
            period=payload.period,
            start_date=payload.start_date or date(today.year, today.month, 1),
        )
        self.session.add(budget)
        self.session.commit()
        self.session.refresh(budget)
        return budget

    def update_budget(self, user_id: int, budget_id: int, payload: BudgetUpdate) -> Budget | None:
        budget = self.get_budget(user_id, budget_id)
        if not budget:
            return None
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(budget, field, value)
        self.session.commit()
        self.session.refresh(budget)
        return budget

    def delete_budget(self, user_id: int, budget_id: int) -> bool:
        budget = self.get_budget(user_id, budget_id)
        if not budget:
            return False
        budget.is_active = False
        self.session.commit()
        return True

    def _enrich(self, budget: Budget) -> BudgetWithUsage:
        today = date.today()
        start = date(today.year, today.month, 1)
        if today.month == 12:
            end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(today.year, today.month + 1, 1) - timedelta(days=1)

        from sqlalchemy import or_
        spent = float(
            self.session.scalar(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    Transaction.user_id == budget.user_id,
                    Transaction.category == budget.category,
                    Transaction.transaction_type == "Expense",
                    Transaction.transaction_date >= start,
                    Transaction.transaction_date <= end,
                    or_(Transaction.is_transfer == False, Transaction.is_transfer == None),
                )
            )
            or 0
        )

        limit = float(budget.amount)
        remaining = max(0.0, limit - spent)
        utilization_pct = round((spent / limit * 100), 1) if limit > 0 else 0.0
        is_exceeded = spent > limit

        if utilization_pct >= 100:
            status = "exceeded"
        elif utilization_pct >= 80:
            status = "warning"
        else:
            status = "healthy"

        return BudgetWithUsage(
            id=budget.id,
            user_id=budget.user_id,
            name=budget.name,
            category=budget.category,
            amount=float(budget.amount),
            period=budget.period,
            start_date=budget.start_date,
            is_active=budget.is_active,
            created_at=budget.created_at,
            spent=spent,
            remaining=remaining,
            utilization_pct=utilization_pct,
            is_exceeded=is_exceeded,
            status=status,
        )
