"""Insights engine — deterministic rules for financial anomalies and changes."""

from datetime import date
from sqlalchemy.orm import Session

from app.fastapi_app.schemas.dashboard import InsightItem
from app.fastapi_app.services.analytics_service import AnalyticsService
from app.fastapi_app.services.dashboard_service import DashboardService
from app.fastapi_app.services.budget_service import BudgetService
from app.fastapi_app.services.subscription_service import SubscriptionService


class InsightsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.analytics = AnalyticsService(session)
        self.dashboard = DashboardService(session)
        self.budgets = BudgetService(session)
        self.subscriptions = SubscriptionService(session)

    def generate_insights(self, user_id: int) -> list[InsightItem]:
        insights: list[InsightItem] = []
        today = date.today()

        # 1. Gather context
        summary = self.analytics.get_summary(user_id)
        current_cats = self.analytics.get_category_breakdown(user_id, today.year, today.month)
        
        prev_month = self.analytics._shift_month(today, 1)
        prev_cats = self.analytics.get_category_breakdown(user_id, prev_month.year, prev_month.month)
        
        budgets = self.budgets.list_budgets(user_id)
        subs = self.subscriptions.list_subscriptions(user_id, confirmed_only=True)
        
        trends = summary.trends

        # 2. Rule: Zero Income Month (High)
        if trends and trends[-1].income <= 0 and trends[-1].expense > 0:
            insights.append(
                InsightItem(
                    type="zero_income",
                    severity="high",
                    title="No Income Detected",
                    explanation="You have recorded expenses this month but no income. Ensure your salary or inbound transfers are logged.",
                    metric="Total Income",
                    value=0.0,
                    recommended_action="Log Income"
                )
            )

        # 3. Rule: Spending Spike (Category level) (High)
        # Compare current category spend to 3-month average
        if current_cats:
            for cat in current_cats:
                # Find historical average for this category
                hist_total = 0.0
                months_counted = 0
                for offset in range(1, 4):
                    m = self.analytics._shift_month(today, offset)
                    c = self.analytics.get_category_breakdown(user_id, m.year, m.month)
                    for hc in c:
                        if hc.category == cat.category:
                            hist_total += hc.amount
                            months_counted += 1
                
                if months_counted > 0:
                    avg = hist_total / 3.0  # use 3 months denominator even if missing to be conservative
                    if avg > 1000 and cat.amount > (avg * 1.5):
                        insights.append(
                            InsightItem(
                                type="spike",
                                severity="high",
                                title=f"Spending Spike in {cat.category}",
                                explanation=f"Your {cat.category} spending is significantly higher than your historical average of ₹{avg:,.2f}.",
                                metric=f"{cat.category} Spend",
                                value=cat.amount,
                                recommended_action="Review Transactions"
                            )
                        )

        # 4. Rule: MoM Expense Change (Medium)
        if len(trends) >= 2:
            current_exp = trends[-1].expense
            prev_exp = trends[-2].expense
            if prev_exp > 0:
                change_pct = ((current_exp - prev_exp) / prev_exp) * 100
                if change_pct > 15:
                    insights.append(
                        InsightItem(
                            type="mom_change",
                            severity="medium",
                            title="Monthly Expenses Increased",
                            explanation=f"Your expenses are up {change_pct:.1f}% compared to last month.",
                            metric="Expense Change",
                            value=current_exp - prev_exp,
                            recommended_action="Check Budget"
                        )
                    )

        # 5. Rule: Budget Near Limit (Medium/High)
        for b in budgets:
            if b.utilization_pct >= 100:
                insights.append(
                    InsightItem(
                        type="budget_risk",
                        severity="high",
                        title=f"Budget Exceeded: {b.name}",
                        explanation=f"You have exceeded your {b.category} budget by ₹{b.spent - b.amount:,.2f}.",
                        metric="Utilization",
                        value=b.utilization_pct,
                        recommended_action="Adjust Spending"
                    )
                )
            elif b.utilization_pct >= 80:
                insights.append(
                    InsightItem(
                        type="budget_risk",
                        severity="medium",
                        title=f"Nearing Budget Limit: {b.name}",
                        explanation=f"You have used {b.utilization_pct}% of your {b.category} budget. Only ₹{b.remaining:,.2f} remaining.",
                        metric="Utilization",
                        value=b.utilization_pct,
                        recommended_action="Pace Spending"
                    )
                )

        # 6. Rule: Savings Rate Decline (Medium)
        if len(trends) >= 2:
            current_rate = trends[-1].savings_rate
            prev_rate = trends[-2].savings_rate
            if prev_rate > 10 and (prev_rate - current_rate) > 5:
                insights.append(
                    InsightItem(
                        type="savings_decline",
                        severity="medium",
                        title="Savings Rate Dropped",
                        explanation=f"Your savings rate dropped from {prev_rate}% to {current_rate}%.",
                        metric="Savings Rate",
                        value=current_rate,
                        recommended_action="Review Top Categories"
                    )
                )

        # 7. Rule: Recurring Expense Summary (Info)
        if subs:
            total_subs = sum(s.amount for s in subs)
            if total_subs > 0:
                insights.append(
                    InsightItem(
                        type="subscriptions",
                        severity="info",
                        title="Fixed Recurring Costs",
                        explanation=f"You have {len(subs)} active subscriptions costing ₹{total_subs:,.2f} per billing cycle.",
                        metric="Recurring Cost",
                        value=total_subs,
                        recommended_action="Audit Subscriptions"
                    )
                )

        # 8. Fallback (Info)
        if not insights:
            insights.append(
                InsightItem(
                    type="stable",
                    severity="info",
                    title="Stable Financials",
                    explanation="No major anomalies or risks detected this month.",
                    metric=None,
                    value=None,
                    recommended_action="Keep it up"
                )
            )

        # Sort insights by severity: high -> medium -> low -> info
        severity_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
        insights.sort(key=lambda x: severity_order.get(x.severity, 4))
        
        return insights
