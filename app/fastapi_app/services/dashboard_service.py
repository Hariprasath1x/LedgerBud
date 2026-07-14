"""Dashboard aggregation and intelligence services."""

from __future__ import annotations

from datetime import date, timedelta
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.fastapi_app.models.transaction import Transaction
from app.fastapi_app.models.wallet import Wallet
from app.fastapi_app.schemas.dashboard import (
    CategoryPoint,
    DashboardSummary,
    HealthScoreBreakdown,
    HealthScoreResponse,
    InsightItem,
    MonthlySeriesPoint,
)


class DashboardService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_summary(self, user_id: int) -> DashboardSummary:
        income = self._sum_transactions(user_id, "Income")
        expense = self._sum_transactions(user_id, "Expense")
        wallet_balance = float(
            self.session.scalar(
                select(func.coalesce(func.sum(Wallet.balance), 0)).where(Wallet.user_id == user_id)
            )
            or 0
        )
        return DashboardSummary(
            total_income=income,
            total_expense=expense,
            savings=income - expense,
            wallet_balance=wallet_balance,
        )

    def get_monthly_trends(self, user_id: int, months: int = 6) -> list[MonthlySeriesPoint]:
        points: list[MonthlySeriesPoint] = []
        today = date.today()
        for offset in range(months - 1, -1, -1):
            month_date = self._shift_month(today, offset)
            income = self._sum_transactions(user_id, "Income", month_date.year, month_date.month)
            expense = self._sum_transactions(user_id, "Expense", month_date.year, month_date.month)
            savings = income - expense
            savings_rate = round((savings / income * 100), 1) if income > 0 else 0
            points.append(
                MonthlySeriesPoint(
                    month=month_date.strftime("%Y-%m"),
                    income=income,
                    expense=expense,
                    savings=savings,
                    savings_rate=savings_rate,
                )
            )
        return points

    def get_category_breakdown(self, user_id: int, year: int | None = None, month: int | None = None) -> list[CategoryPoint]:
        today = date.today()
        year = year or today.year
        month = month or today.month
        start, end = self._month_range(year, month)

        from sqlalchemy import or_
        statement = (
            select(Transaction.category, func.count(Transaction.id).label("count"), func.sum(Transaction.amount).label("amount"))
            .where(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "Expense",
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
                or_(Transaction.is_transfer == False, Transaction.is_transfer == None),
            )
            .group_by(Transaction.category)
            .order_by(func.sum(Transaction.amount).desc())
        )
        rows = self.session.execute(statement).all()
        total = sum(float(row.amount or 0) for row in rows)

        categories: list[CategoryPoint] = []
        for row in rows:
            categories.append(
                CategoryPoint(
                    category=row.category or "Uncategorized",
                    amount=float(row.amount or 0),
                    count=int(row.count or 0),
                    percentage=round((float(row.amount or 0) / total * 100), 1) if total > 0 else 0,
                )
            )
        return categories

    def get_top_merchants(self, user_id: int, limit: int = 5) -> list[dict[str, float | int | str]]:
        from sqlalchemy import or_
        statement = (
            select(Transaction.merchant_name, func.sum(Transaction.amount).label("amount"), func.count(Transaction.id).label("count"))
            .where(
                Transaction.user_id == user_id, 
                Transaction.transaction_type == "Expense",
                or_(Transaction.is_transfer == False, Transaction.is_transfer == None),
            )
            .group_by(Transaction.merchant_name)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(limit)
        )
        return [
            {"merchant": row.merchant_name, "amount": float(row.amount or 0), "count": int(row.count or 0)}
            for row in self.session.execute(statement).all()
        ]

    def calculate_health_score(self, user_id: int) -> HealthScoreResponse:
        summary = self.get_summary(user_id)
        categories = self.get_category_breakdown(user_id)
        transactions = self._transaction_records(user_id)

        income = summary.total_income
        expense = summary.total_expense
        savings_rate = round((summary.savings / income * 100), 1) if income > 0 else 0

        savings_score = 0
        if savings_rate >= 30:
            savings_score = 40
        elif savings_rate >= 20:
            savings_score = 30
        elif savings_rate >= 10:
            savings_score = 20
        elif savings_rate >= 0:
            savings_score = 10

        budget_discipline = 0
        expense_ratio = round((expense / income * 100), 1) if income > 0 else 100
        if income <= 0:
            budget_discipline = 0
        elif expense_ratio <= 60:
            budget_discipline = 30
        elif expense_ratio <= 75:
            budget_discipline = 24
        elif expense_ratio <= 90:
            budget_discipline = 16
        else:
            budget_discipline = 8

        spending_behavior = 15
        if categories:
            top_pct = categories[0].percentage
            if top_pct > 70:
                spending_behavior = 5
            elif top_pct > 50:
                spending_behavior = 10

        if transactions:
            total_spend = sum(record["amount"] for record in transactions)
            weekend_spend = sum(record["amount"] for record in transactions if record["weekday"] >= 5)
            weekend_share = weekend_spend / max(total_spend, 1)
            if weekend_share > 0.35:
                spending_behavior = max(5, spending_behavior - 2)

        score = max(0, min(100, savings_score + budget_discipline + spending_behavior))
        if score >= 80:
            grade, label = "A", "Excellent"
        elif score >= 65:
            grade, label = "B", "Good"
        elif score >= 50:
            grade, label = "C", "Fair"
        elif score >= 35:
            grade, label = "D", "Needs Attention"
        else:
            grade, label = "F", "Poor"

        suggestions = self._health_suggestions(savings_rate, expense_ratio, categories)
        return HealthScoreResponse(
            score=score,
            grade=grade,
            label=label,
            breakdown=HealthScoreBreakdown(
                savings_ratio=savings_score,
                budget_discipline=budget_discipline,
                spending_behavior=spending_behavior,
            ),
            suggestions=suggestions,
        )

    def generate_insights(self, user_id: int) -> list[InsightItem]:
        summary = self.get_summary(user_id)
        current_categories = self.get_category_breakdown(user_id)
        previous_month = self._shift_month(date.today(), 1)
        previous_categories = self.get_category_breakdown(user_id, previous_month.year, previous_month.month)

        insights: list[InsightItem] = []

        if summary.total_income > 0 and summary.savings / max(summary.total_income, 1) < 0.2:
            insights.append(
                InsightItem(
                    type="warning",
                    title="Low Savings Rate",
                    message=f"You are saving only {round(summary.savings / summary.total_income * 100, 1)}% of income this month.",
                )
            )

        if current_categories:
            top = current_categories[0]
            insights.append(
                InsightItem(
                    type="info",
                    title=f"Highest Spending Category: {top.category}",
                    message=f"{top.category} accounts for {top.percentage}% of this month's spending.",
                )
            )

        if current_categories and previous_categories:
            previous_map = {item.category: item.amount for item in previous_categories}
            for item in current_categories[:3]:
                prior = previous_map.get(item.category, 0)
                if prior > 0 and item.amount > prior * 1.15:
                    delta = round((item.amount - prior) / prior * 100, 1)
                    insights.append(
                        InsightItem(
                            type="warning",
                            title=f"{item.category} Increased",
                            message=f"{item.category} spend is up {delta}% compared to last month.",
                        )
                    )

        if not insights:
            insights.append(
                InsightItem(
                    type="success",
                    title="Stable Spending",
                    message="Your spending pattern looks steady this month with no major anomalies detected.",
                )
            )
        return insights

    def dashboard_payload(self, user_id: int) -> dict:
        summary = self.get_summary(user_id)
        trends = self.get_monthly_trends(user_id)
        categories = self.get_category_breakdown(user_id)
        health = self.calculate_health_score(user_id)
        insights = self.generate_insights(user_id)
        top_merchants = self.get_top_merchants(user_id)
        return {
            "summary": summary,
            "monthly_trends": trends,
            "category_breakdown": categories,
            "top_merchants": top_merchants,
            "health_score": health,
            "insights": insights,
        }

    def _transaction_records(self, user_id: int) -> list[dict[str, object]]:
        from sqlalchemy import or_
        statement = select(
            Transaction.amount,
            Transaction.transaction_date,
            Transaction.transaction_type,
        ).where(
            Transaction.user_id == user_id,
            or_(Transaction.is_transfer == False, Transaction.is_transfer == None),
        )
        rows = self.session.execute(statement).all()
        if not rows:
            return []
        return [
            {
                "amount": float(amount or 0),
                "transaction_date": transaction_date,
                "transaction_type": transaction_type,
                "weekday": transaction_date.weekday(),
            }
            for amount, transaction_date, transaction_type in rows
        ]

    def _sum_transactions(self, user_id: int, transaction_type: str, year: int | None = None, month: int | None = None) -> float:
        from sqlalchemy import or_
        statement = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.transaction_type == transaction_type,
            or_(Transaction.is_transfer == False, Transaction.is_transfer == None),
        )
        if year and month:
            start, end = self._month_range(year, month)
            statement = statement.where(Transaction.transaction_date >= start, Transaction.transaction_date <= end)
        return float(self.session.scalar(statement) or 0)

    def _month_range(self, year: int, month: int) -> tuple[date, date]:
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(year, month + 1, 1) - timedelta(days=1)
        return start, end

    def _shift_month(self, base: date, months_back: int) -> date:
        month = base.month - months_back
        year = base.year
        while month <= 0:
            month += 12
            year -= 1
        return date(year, month, 1)

    def _health_suggestions(self, savings_rate: float, expense_ratio: float, categories: list[CategoryPoint]) -> list[str]:
        suggestions: list[str] = []
        if savings_rate < 20:
            suggestions.append("Increase monthly savings to at least 20% of income.")
        if expense_ratio > 75:
            suggestions.append("Reduce discretionary spending so expenses stay under 75% of income.")
        if categories and categories[0].percentage > 50:
            suggestions.append(f"Review {categories[0].category} because it dominates your spending.")
        if not suggestions:
            suggestions.append("Maintain current habits and keep tracking changes monthly.")
        return suggestions
