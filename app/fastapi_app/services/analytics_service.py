"""Analytics service — trends, categories, merchants, what-if simulation."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.fastapi_app.models.transaction import Transaction
from app.fastapi_app.schemas.analytics import (
    AnalyticsSummary,
    CategoryBreakdown,
    MerchantPoint,
    TrendPoint,
    WhatIfRequest,
    WhatIfResponse,
)


class AnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_trends(self, user_id: int, months: int = 6) -> list[TrendPoint]:
        points: list[TrendPoint] = []
        today = date.today()
        for offset in range(months - 1, -1, -1):
            month_date = self._shift_month(today, offset)
            income = self._sum(user_id, "Income", month_date.year, month_date.month)
            expense = self._sum(user_id, "Expense", month_date.year, month_date.month)
            savings = income - expense
            savings_rate = round((savings / income * 100), 1) if income > 0 else 0.0
            points.append(
                TrendPoint(
                    month=month_date.strftime("%Y-%m"),
                    income=income,
                    expense=expense,
                    savings=savings,
                    savings_rate=savings_rate,
                )
            )
        return points

    def get_category_breakdown(self, user_id: int, year: int | None = None, month: int | None = None) -> list[CategoryBreakdown]:
        today = date.today()
        year = year or today.year
        month = month or today.month
        start, end = self._month_range(year, month)

        from sqlalchemy import or_
        rows = self.session.execute(
            select(
                Transaction.category,
                func.count(Transaction.id).label("cnt"),
                func.sum(Transaction.amount).label("total"),
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "Expense",
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
                or_(Transaction.is_transfer == False, Transaction.is_transfer == None),
            )
            .group_by(Transaction.category)
            .order_by(func.sum(Transaction.amount).desc())
        ).all()

        grand_total = sum(float(r.total or 0) for r in rows)
        return [
            CategoryBreakdown(
                category=r.category or "Uncategorized",
                amount=float(r.total or 0),
                count=int(r.cnt or 0),
                percentage=round(float(r.total or 0) / grand_total * 100, 1) if grand_total > 0 else 0.0,
            )
            for r in rows
        ]

    def get_top_merchants(self, user_id: int, limit: int = 10) -> list[MerchantPoint]:
        today = date.today()
        start, end = self._month_range(today.year, today.month)
        from sqlalchemy import or_
        rows = self.session.execute(
            select(
                Transaction.merchant_name,
                func.sum(Transaction.amount).label("total"),
                func.count(Transaction.id).label("cnt"),
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "Expense",
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
                or_(Transaction.is_transfer == False, Transaction.is_transfer == None),
            )
            .group_by(Transaction.merchant_name)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(limit)
        ).all()
        return [
            MerchantPoint(merchant=r.merchant_name or "Unknown", amount=float(r.total or 0), count=int(r.cnt or 0))
            for r in rows
        ]

    def get_summary(self, user_id: int) -> AnalyticsSummary:
        return AnalyticsSummary(
            trends=self.get_trends(user_id),
            category_breakdown=self.get_category_breakdown(user_id),
            top_merchants=self.get_top_merchants(user_id),
        )

    def whatif_simulation(self, user_id: int, payload: WhatIfRequest) -> WhatIfResponse:
        today = date.today()
        start, end = self._month_range(today.year, today.month)

        current_expense = self._sum(user_id, "Expense")
        current_income = self._sum(user_id, "Income")
        current_savings = current_income - current_expense

        new_expense = max(0.0, current_expense - payload.reduce_by)
        new_savings = current_income - new_expense
        new_savings_rate = (new_savings / current_income * 100) if current_income > 0 else 0.0
        yearly_savings = new_savings * 12
        r = payload.interest_rate / 100
        n = payload.years
        investment_value = yearly_savings * ((((1 + r) ** n) - 1) / r) if yearly_savings > 0 and r > 0 else 0.0

        return WhatIfResponse(
            current_expense=current_expense,
            new_expense=new_expense,
            current_savings=current_savings,
            new_savings=new_savings,
            new_savings_rate=round(new_savings_rate, 1),
            yearly_savings=yearly_savings,
            investment_value=round(investment_value, 2),
            reduction=payload.reduce_by,
            years=payload.years,
            interest_rate=payload.interest_rate,
        )

    # --- helpers ---

    def _sum(self, user_id: int, txn_type: str, year: int | None = None, month: int | None = None) -> float:
        from sqlalchemy import or_
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == txn_type,
            or_(Transaction.is_transfer == False, Transaction.is_transfer == None),
        )
        if year and month:
            start, end = self._month_range(year, month)
            stmt = stmt.where(Transaction.transaction_date >= start, Transaction.transaction_date <= end)
        return float(self.session.scalar(stmt) or 0)

    def _month_range(self, year: int, month: int) -> tuple[date, date]:
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) - timedelta(days=1) if month == 12 else date(year, month + 1, 1) - timedelta(days=1)
        return start, end

    def _shift_month(self, base: date, months_back: int) -> date:
        month = base.month - months_back
        year = base.year
        while month <= 0:
            month += 12
            year -= 1
        return date(year, month, 1)
