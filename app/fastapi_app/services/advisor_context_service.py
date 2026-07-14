"""AI Advisor Context Service — compiles summarized context for LLM."""

from sqlalchemy.orm import Session
from datetime import date

from app.fastapi_app.services.dashboard_service import DashboardService
from app.fastapi_app.services.analytics_service import AnalyticsService
from app.fastapi_app.services.budget_service import BudgetService
from app.fastapi_app.services.goal_service import GoalService
from app.fastapi_app.services.subscription_service import SubscriptionService
from app.fastapi_app.services.net_worth_service import NetWorthService
from app.fastapi_app.services.wallet_service import WalletService
from app.fastapi_app.services.insights_service import InsightsService


class AdvisorContextService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.dashboard = DashboardService(session)
        self.analytics = AnalyticsService(session)
        self.budgets = BudgetService(session)
        self.goals = GoalService(session)
        self.subs = SubscriptionService(session)
        self.net_worth = NetWorthService(session)
        self.wallets = WalletService(session)
        self.insights = InsightsService(session)

    def get_context(self, user_id: int) -> dict:
        """Build a compact, privacy-safe summary of user financials."""
        today = date.today()
        
        # 1. Wallet Balances
        wallet_summary = self.wallets.wallet_summary(user_id)
        
        # 2. Income/Expense & Trends
        summary = self.dashboard.get_summary(user_id)
        trends = self.dashboard.get_monthly_trends(user_id, months=3)
        categories = self.dashboard.get_category_breakdown(user_id, today.year, today.month)
        
        # 3. Budgets
        active_budgets = self.budgets.list_budgets(user_id)
        budget_summary = [
            {"name": b.name, "spent": b.spent, "limit": b.amount, "utilization": b.utilization_pct}
            for b in active_budgets
        ]
        
        # 4. Goals
        active_goals = self.goals.list_goals(user_id)
        goal_summary = [
            {"name": g.name, "target": float(g.target_amount), "current": float(g.current_amount), "progress": g.progress_percentage}
            for g in active_goals if g.status == "active"
        ]
        
        # 5. Subscriptions
        subscriptions = self.subs.list_subscriptions(user_id, confirmed_only=True)
        sub_total = sum(s.amount for s in subscriptions)
        
        # 6. Health Score
        health = self.dashboard.calculate_health_score(user_id)
        
        # 7. Net Worth
        nw_summary = self.net_worth.get_summary(user_id)
        
        # 8. Insights Engine Findings
        insights = self.insights.generate_insights(user_id)
        insight_summary = [
            {"severity": i.severity, "title": i.title, "explanation": i.explanation}
            for i in insights
        ]

        # Assemble compact context
        context = {
            "current_month": f"{today.year}-{today.month:02d}",
            "wallet_balance": wallet_summary["total_balance"],
            "net_worth": nw_summary.net_worth,
            "assets": nw_summary.total_assets,
            "liabilities": nw_summary.total_liabilities,
            "monthly_income": summary.total_income,
            "monthly_expense": summary.total_expense,
            "monthly_savings": summary.savings,
            "savings_rate_percent": round((summary.savings / summary.total_income * 100) if summary.total_income > 0 else 0, 1),
            "historical_trends": [
                {"month": t.month, "income": t.income, "expense": t.expense, "savings_rate": t.savings_rate}
                for t in trends
            ],
            "top_categories": [
                {"category": c.category, "amount": c.amount, "percent": c.percentage}
                for c in categories[:5]
            ],
            "budgets": budget_summary,
            "goals": goal_summary,
            "recurring_subscriptions_total": sub_total,
            "health_score": health.score,
            "health_grade": health.grade,
            "anomalies_and_insights": insight_summary
        }
        
        return context
