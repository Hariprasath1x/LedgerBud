"""FIRE Intelligence Engine — 10-step calculation service.

All financial data is auto-fetched from existing services.
Only user-configurable inputs (age, return rate, inflation, lifestyle)
are accepted as parameters.
"""

from __future__ import annotations

import math
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.fastapi_app.models.fire import FireAnalysis
from app.fastapi_app.repositories.fire_repository import FireRepository
from app.fastapi_app.schemas.fire import (
    FireCalculationResult,
    FireDashboardResponse,
    FireHistoryItem,
    FireScenario,
    FireScoreBreakdown,
    FireSettings,
    WealthProjectionPoint,
)
from app.fastapi_app.services.dashboard_service import DashboardService
from app.fastapi_app.services.net_worth_service import NetWorthService
from app.fastapi_app.services.budget_service import BudgetService
from app.fastapi_app.services.goal_service import GoalService
from app.fastapi_app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

# Lifestyle multipliers applied to annual expenses for corpus calculation
LIFESTYLE_MULTIPLIERS = {
    "Lean": 0.80,
    "Moderate": 1.00,
    "Comfortable": 1.25,
    "Luxury": 1.60,
}


class FIREService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = FireRepository(session)
        self.dashboard = DashboardService(session)
        self.net_worth = NetWorthService(session)
        self.budgets = BudgetService(session)
        self.goals = GoalService(session)
        self.subs = SubscriptionService(session)

    # ─────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────

    def calculate(self, user_id: int, settings: FireSettings) -> FireCalculationResult:
        """Run the full 10-step FIRE calculation and persist a snapshot."""
        result = self._run_engine(user_id, settings)

        # Persist
        analysis = FireAnalysis(
            user_id=user_id,
            current_age=settings.current_age,
            retirement_target_age=settings.retirement_target_age,
            investment_return=settings.investment_return,
            inflation_rate=settings.inflation_rate,
            lifestyle=settings.lifestyle,
            current_net_worth=result.current_net_worth,
            annual_income=result.annual_income,
            annual_expenses=result.annual_expenses,
            annual_savings=result.annual_savings,
            savings_rate=result.savings_rate,
            fire_target_corpus=result.fire_target_corpus,
            fire_progress=result.fire_progress,
            fire_score=result.fire_score,
            estimated_fire_age=result.estimated_fire_age,
            years_remaining=result.years_remaining,
            required_monthly_investment=result.required_monthly_investment,
            wealth_projection=[p.model_dump() for p in result.wealth_projection],
            scenarios=[s.model_dump() for s in result.scenarios],
            strengths=result.strengths,
            weaknesses=result.weaknesses,
        )
        self.repo.save(analysis)
        return result

    def get_dashboard(self, user_id: int) -> FireDashboardResponse:
        """Return the latest stored FIRE analysis or an empty state."""
        latest = self.repo.get_latest(user_id)
        if not latest:
            return FireDashboardResponse(has_data=False)

        result = self._hydrate_from_db(latest)
        return FireDashboardResponse(
            has_data=True,
            result=result,
            last_calculated=latest.created_at,
        )

    def get_history(self, user_id: int, limit: int = 20) -> list[FireHistoryItem]:
        """Return paginated history of FIRE calculations."""
        records = self.repo.list_history(user_id, limit=limit)
        return [FireHistoryItem.model_validate(r) for r in records]

    def build_fire_context(self, user_id: int) -> dict:
        """Build FIRE-specific context for the AI coach."""
        latest = self.repo.get_latest(user_id)
        if not latest:
            # Fall back to live calculation with defaults
            try:
                settings = FireSettings()
                result = self._run_engine(user_id, settings)
                return self._result_to_context(result)
            except Exception:
                return {}

        return {
            "current_age": latest.current_age,
            "retirement_target_age": latest.retirement_target_age,
            "current_net_worth": round(latest.current_net_worth, 2),
            "annual_income": round(latest.annual_income, 2),
            "annual_expenses": round(latest.annual_expenses, 2),
            "savings_rate_percent": round(latest.savings_rate, 1),
            "fire_score": round(latest.fire_score, 1),
            "fire_progress_percent": round(latest.fire_progress, 1),
            "fire_target_corpus": round(latest.fire_target_corpus, 2),
            "estimated_fire_age": round(latest.estimated_fire_age, 1),
            "years_remaining": round(latest.years_remaining, 1),
            "required_monthly_investment": round(latest.required_monthly_investment, 2),
            "expected_return_percent": latest.investment_return,
            "inflation_rate_percent": latest.inflation_rate,
            "lifestyle": latest.lifestyle,
            "strengths": (latest.strengths or [])[:3],
            "weaknesses": (latest.weaknesses or [])[:3],
        }

    # ─────────────────────────────────────────────────────────────────────
    # FIRE Engine — 10 Steps
    # ─────────────────────────────────────────────────────────────────────

    def _run_engine(self, user_id: int, settings: FireSettings) -> FireCalculationResult:
        """Execute all 10 FIRE calculation steps."""

        # ── STEP 1: Fetch & annualise existing data ───────────────────────
        trends = self.dashboard.get_monthly_trends(user_id, months=12)
        nw_summary = self.net_worth.get_summary(user_id)
        active_budgets = self.budgets.list_budgets(user_id)
        active_goals = self.goals.list_goals(user_id)
        subscriptions = self.subs.list_subscriptions(user_id, confirmed_only=True)
        health = self.dashboard.calculate_health_score(user_id)
        categories = self.dashboard.get_category_breakdown(user_id)

        # Annualise from monthly trend data (use available months, min 1)
        months_with_data = [m for m in trends if m.income > 0 or m.expense > 0]
        n_months = max(len(months_with_data), 1)

        total_income_sum = sum(m.income for m in trends)
        total_expense_sum = sum(m.expense for m in trends)

        monthly_income = total_income_sum / n_months if n_months > 0 else 0
        monthly_expenses = total_expense_sum / n_months if n_months > 0 else 0
        monthly_savings = monthly_income - monthly_expenses

        annual_income = monthly_income * 12
        annual_expenses = monthly_expenses * 12
        annual_savings = monthly_savings * 12

        current_net_worth = float(nw_summary.net_worth)
        total_assets = float(nw_summary.total_assets)
        total_liabilities = float(nw_summary.total_liabilities)

        sub_monthly_total = sum(float(s.amount) for s in subscriptions)

        top_category = categories[0].category if categories else "N/A"

        # Goal progress
        active_goal_list = [g for g in active_goals if g.status == "active"]
        if active_goal_list:
            goal_progress_avg = sum(
                min(float(g.current_amount) / max(float(g.target_amount), 1) * 100, 100)
                for g in active_goal_list
            ) / len(active_goal_list)
        else:
            goal_progress_avg = 0.0

        # ── STEP 2: Savings Rate ──────────────────────────────────────────
        savings_rate = (annual_savings / annual_income * 100) if annual_income > 0 else 0.0
        savings_rate = max(0.0, savings_rate)

        # ── STEP 3: Debt Ratio ────────────────────────────────────────────
        debt_ratio = (total_liabilities / total_assets * 100) if total_assets > 0 else 0.0

        # ── STEP 4: FIRE Target Corpus (25× rule with lifestyle multiplier) ─
        lifestyle_multiplier = LIFESTYLE_MULTIPLIERS.get(settings.lifestyle, 1.0)
        adjusted_annual_expenses = annual_expenses * lifestyle_multiplier
        fire_target_corpus = adjusted_annual_expenses * 25

        # ── STEP 5: FIRE Progress ─────────────────────────────────────────
        fire_progress = (
            (current_net_worth / fire_target_corpus * 100)
            if fire_target_corpus > 0
            else 0.0
        )
        fire_progress = min(fire_progress, 100.0)

        # ── STEP 6: FIRE Readiness Score ──────────────────────────────────
        score_breakdown, fire_score = self._compute_fire_score(
            savings_rate=savings_rate,
            health_score=float(health.score),
            debt_ratio=debt_ratio,
            trends=trends,
            active_budgets=active_budgets,
        )

        # ── STEP 7: Wealth Projection ─────────────────────────────────────
        r = settings.investment_return / 100
        inf = settings.inflation_rate / 100
        monthly_sip_current = max(monthly_savings, 0)

        wealth_projection = self._project_wealth(
            current_net_worth=current_net_worth,
            monthly_investment=monthly_sip_current,
            annual_return=r,
            inflation=inf,
            current_age=settings.current_age,
            horizons=[5, 10, 15, 20, 25],
            target_corpus=fire_target_corpus,
        )

        # ── STEP 8: Estimated FIRE Age ────────────────────────────────────
        estimated_fire_age, years_to_fire = self._estimate_fire_age(
            current_net_worth=current_net_worth,
            monthly_investment=monthly_sip_current,
            annual_return=r,
            inflation=inf,
            fire_target_corpus=fire_target_corpus,
            current_age=settings.current_age,
            max_years=60,
        )
        years_remaining = max(0.0, estimated_fire_age - settings.current_age)

        # ── STEP 9: Required Monthly Investment ───────────────────────────
        years_to_target = max(settings.retirement_target_age - settings.current_age, 1)
        required_monthly_investment = self._calc_required_sip(
            current_net_worth=current_net_worth,
            target=fire_target_corpus,
            annual_return=r,
            years=years_to_target,
        )

        # ── STEP 10: Scenario Analysis ────────────────────────────────────
        scenarios = self._build_scenarios(
            current_net_worth=current_net_worth,
            monthly_investment=monthly_sip_current,
            fire_target_corpus=fire_target_corpus,
            current_age=settings.current_age,
            retirement_target_age=settings.retirement_target_age,
            base_return=settings.investment_return,
            base_inflation=settings.inflation_rate,
        )

        # ── Strengths & Weaknesses ────────────────────────────────────────
        strengths, weaknesses = self._generate_observations(
            savings_rate=savings_rate,
            debt_ratio=debt_ratio,
            fire_score=fire_score,
            fire_progress=fire_progress,
            health_score=float(health.score),
            active_budgets=active_budgets,
            sub_monthly_total=sub_monthly_total,
            top_category=top_category,
            annual_income=annual_income,
            goal_progress_avg=goal_progress_avg,
        )

        # ── Status Label ──────────────────────────────────────────────────
        status_label = self._status_label(
            estimated_fire_age=estimated_fire_age,
            retirement_target_age=settings.retirement_target_age,
            fire_progress=fire_progress,
        )

        return FireCalculationResult(
            settings=settings,
            current_net_worth=current_net_worth,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            annual_income=annual_income,
            annual_expenses=annual_expenses,
            annual_savings=annual_savings,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            monthly_savings=monthly_savings,
            savings_rate=round(savings_rate, 2),
            debt_ratio=round(debt_ratio, 2),
            financial_health_score=float(health.score),
            fire_target_corpus=round(fire_target_corpus, 2),
            fire_progress=round(fire_progress, 2),
            fire_score=round(fire_score, 2),
            score_breakdown=score_breakdown,
            estimated_fire_age=round(estimated_fire_age, 1),
            years_remaining=round(years_remaining, 1),
            required_monthly_investment=round(required_monthly_investment, 2),
            wealth_projection=wealth_projection,
            scenarios=scenarios,
            strengths=strengths,
            weaknesses=weaknesses,
            subscription_monthly_total=round(sub_monthly_total, 2),
            goal_progress_avg=round(goal_progress_avg, 1),
            top_expense_category=top_category,
            status_label=status_label,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Step 6 — Score computation
    # ─────────────────────────────────────────────────────────────────────

    def _compute_fire_score(
        self,
        savings_rate: float,
        health_score: float,
        debt_ratio: float,
        trends: list,
        active_budgets: list,
    ) -> tuple[FireScoreBreakdown, float]:

        # Savings Rate — max 30
        if savings_rate >= 40:
            sr_score = 30.0
        elif savings_rate >= 30:
            sr_score = 25.0
        elif savings_rate >= 20:
            sr_score = 18.0
        elif savings_rate >= 10:
            sr_score = 10.0
        else:
            sr_score = max(0.0, savings_rate * 0.5)

        # Financial Health Score — max 25
        hs_score = (health_score / 100) * 25

        # Debt Ratio — max 15 (lower is better)
        if debt_ratio <= 0:
            dr_score = 15.0
        elif debt_ratio <= 20:
            dr_score = 13.0
        elif debt_ratio <= 40:
            dr_score = 9.0
        elif debt_ratio <= 60:
            dr_score = 4.0
        else:
            dr_score = 0.0

        # Net Worth Growth — max 15 (from trend data)
        nw_growth_score = 0.0
        monthly_savings_list = [m.savings for m in trends if m.income > 0]
        if len(monthly_savings_list) >= 3:
            positive_months = sum(1 for s in monthly_savings_list if s > 0)
            consistency = positive_months / len(monthly_savings_list)
            nw_growth_score = consistency * 15.0

        # Investment Discipline — max 10 (savings rate consistency)
        inv_disc_score = 0.0
        if len(monthly_savings_list) >= 2:
            positive_months = sum(1 for s in monthly_savings_list if s > 0)
            inv_disc_score = (positive_months / len(monthly_savings_list)) * 10.0

        # Budget Discipline — max 5
        budget_disc_score = 0.0
        if active_budgets:
            healthy_count = sum(1 for b in active_budgets if b.status == "healthy")
            budget_disc_score = (healthy_count / len(active_budgets)) * 5.0

        total = sr_score + hs_score + dr_score + nw_growth_score + inv_disc_score + budget_disc_score
        total = round(min(max(total, 0.0), 100.0), 2)

        breakdown = FireScoreBreakdown(
            savings_rate_score=round(sr_score, 2),
            health_score_contribution=round(hs_score, 2),
            debt_ratio_score=round(dr_score, 2),
            net_worth_growth_score=round(nw_growth_score, 2),
            investment_discipline_score=round(inv_disc_score, 2),
            budget_discipline_score=round(budget_disc_score, 2),
        )
        return breakdown, total

    # ─────────────────────────────────────────────────────────────────────
    # Step 7 — Compound wealth projection
    # ─────────────────────────────────────────────────────────────────────

    def _project_wealth(
        self,
        current_net_worth: float,
        monthly_investment: float,
        annual_return: float,
        inflation: float,
        current_age: int,
        horizons: list[int],
        target_corpus: float,
    ) -> list[WealthProjectionPoint]:
        """
        FV = PV*(1+r)^n + PMT * [(1+r)^n - 1] / r
        Both nominal and real (inflation-adjusted) values.
        """
        points = []
        for years in horizons:
            fv_nominal = self._fv(current_net_worth, monthly_investment, annual_return, years)
            real_discount = (1 + inflation) ** years
            fv_real = fv_nominal / real_discount
            points.append(
                WealthProjectionPoint(
                    year=date.today().year + years,
                    age=current_age + years,
                    nominal_wealth=round(fv_nominal, 2),
                    real_wealth=round(fv_real, 2),
                    target_corpus=round(target_corpus, 2),
                )
            )
        return points

    # ─────────────────────────────────────────────────────────────────────
    # Step 8 — Estimate FIRE age
    # ─────────────────────────────────────────────────────────────────────

    def _estimate_fire_age(
        self,
        current_net_worth: float,
        monthly_investment: float,
        annual_return: float,
        inflation: float,
        fire_target_corpus: float,
        current_age: int,
        max_years: int = 60,
    ) -> tuple[float, float]:
        """Binary-search for the year where projected nominal wealth >= target corpus."""
        if fire_target_corpus <= 0:
            return float(current_age), 0.0

        if current_net_worth >= fire_target_corpus:
            return float(current_age), 0.0

        for years in range(1, max_years + 1):
            projected = self._fv(current_net_worth, monthly_investment, annual_return, years)
            if projected >= fire_target_corpus:
                # Linear interpolation for fractional year
                if years > 1:
                    prev = self._fv(current_net_worth, monthly_investment, annual_return, years - 1)
                    if projected != prev:
                        fraction = (fire_target_corpus - prev) / (projected - prev)
                        years_exact = (years - 1) + fraction
                    else:
                        years_exact = float(years)
                else:
                    years_exact = float(years)
                return current_age + years_exact, years_exact

        # Cannot reach FIRE within max_years — return extrapolated estimate
        return float(current_age + max_years), float(max_years)

    # ─────────────────────────────────────────────────────────────────────
    # Step 9 — Required SIP
    # ─────────────────────────────────────────────────────────────────────

    def _calc_required_sip(
        self,
        current_net_worth: float,
        target: float,
        annual_return: float,
        years: int,
    ) -> float:
        """
        Solve PMT such that:
          FV = PV*(1+r)^n + PMT * [(1+r)^n - 1] / r  == target
        => PMT = (target - PV*(1+r)^n) / [(1+r)^n - 1] * r
        r is monthly rate.
        """
        if years <= 0 or target <= 0:
            return 0.0
        r_monthly = annual_return / 12
        n = years * 12
        if r_monthly == 0:
            # Simple case: no return
            gap = max(target - current_net_worth, 0)
            return round(gap / n, 2)
        growth_factor = (1 + r_monthly) ** n
        pv_grown = current_net_worth * growth_factor
        remaining = target - pv_grown
        if remaining <= 0:
            return 0.0
        annuity_factor = (growth_factor - 1) / r_monthly
        sip = remaining / annuity_factor
        return max(round(sip, 2), 0.0)

    # ─────────────────────────────────────────────────────────────────────
    # Step 10 — Scenarios
    # ─────────────────────────────────────────────────────────────────────

    def _build_scenarios(
        self,
        current_net_worth: float,
        monthly_investment: float,
        fire_target_corpus: float,
        current_age: int,
        retirement_target_age: int,
        base_return: float,
        base_inflation: float,
    ) -> list[FireScenario]:
        params = [
            ("Conservative", base_return - 3.0, base_inflation + 1.0),
            ("Moderate", base_return, base_inflation),
            ("Aggressive", base_return + 3.0, max(base_inflation - 1.0, 1.0)),
        ]
        scenarios = []
        for name, ret, inf in params:
            ret = max(ret, 1.0)
            r = ret / 100
            target = fire_target_corpus  # corpus stays same (expenses don't change)
            fire_age, _ = self._estimate_fire_age(
                current_net_worth, monthly_investment, r, inf / 100, target, current_age
            )
            years_to_target = max(retirement_target_age - current_age, 1)
            sip = self._calc_required_sip(current_net_worth, target, r, years_to_target)
            scenarios.append(
                FireScenario(
                    name=name,
                    expected_return=round(ret, 1),
                    inflation_rate=round(inf, 1),
                    fire_target_corpus=round(target, 2),
                    estimated_fire_age=round(fire_age, 1),
                    years_remaining=round(max(fire_age - current_age, 0), 1),
                    monthly_investment_required=round(sip, 2),
                )
            )
        return scenarios

    # ─────────────────────────────────────────────────────────────────────
    # Helper calculations
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _fv(
        present_value: float,
        monthly_investment: float,
        annual_return: float,
        years: int,
    ) -> float:
        """Future value of lump sum + monthly contributions."""
        r = annual_return / 12  # monthly rate
        n = years * 12
        if r == 0:
            return present_value + monthly_investment * n
        growth = (1 + r) ** n
        return present_value * growth + monthly_investment * (growth - 1) / r

    # ─────────────────────────────────────────────────────────────────────
    # Strengths & Weaknesses
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _generate_observations(
        savings_rate: float,
        debt_ratio: float,
        fire_score: float,
        fire_progress: float,
        health_score: float,
        active_budgets: list,
        sub_monthly_total: float,
        top_category: str,
        annual_income: float,
        goal_progress_avg: float,
    ) -> tuple[list[str], list[str]]:
        strengths: list[str] = []
        weaknesses: list[str] = []

        # Savings rate
        if savings_rate >= 40:
            strengths.append(f"Excellent savings rate of {savings_rate:.1f}% — well above the FIRE threshold of 30%.")
        elif savings_rate >= 30:
            strengths.append(f"Good savings rate of {savings_rate:.1f}% — meets the minimum FIRE threshold.")
        elif savings_rate >= 15:
            weaknesses.append(
                f"Savings rate of {savings_rate:.1f}% is below the FIRE threshold of 30%. Increase monthly savings to accelerate your journey."
            )
        else:
            weaknesses.append(
                f"Low savings rate of {savings_rate:.1f}%. FIRE requires at least 30% savings rate. Review all expense categories."
            )

        # Debt ratio
        if debt_ratio <= 20 and debt_ratio >= 0:
            strengths.append(f"Healthy debt ratio of {debt_ratio:.1f}% — liabilities are well-controlled.")
        elif debt_ratio > 60:
            weaknesses.append(
                f"High debt ratio of {debt_ratio:.1f}%. Focus on paying down liabilities before aggressively investing."
            )

        # Health score
        if health_score >= 75:
            strengths.append(f"Strong Financial Health Score of {health_score:.0f}/100 — indicates overall financial discipline.")
        elif health_score < 50:
            weaknesses.append(
                f"Financial Health Score of {health_score:.0f}/100 is below average. Address budget overruns and spending habits."
            )

        # FIRE progress
        if fire_progress >= 25:
            strengths.append(f"You are {fire_progress:.1f}% of the way to your FIRE corpus — great momentum!")
        elif fire_progress < 5:
            weaknesses.append("FIRE progress is very early-stage. Focus on building net worth through assets and investments.")

        # Budget discipline
        if active_budgets:
            healthy_budgets = [b for b in active_budgets if b.status == "healthy"]
            if len(healthy_budgets) == len(active_budgets):
                strengths.append("All budget categories are within healthy limits — strong budget discipline.")
            exceeded = [b for b in active_budgets if b.status == "exceeded"]
            if exceeded:
                names = ", ".join(b.name for b in exceeded[:3])
                weaknesses.append(f"Budget exceeded in: {names}. Overspending reduces your investable surplus.")

        # Subscriptions
        if annual_income > 0 and sub_monthly_total > 0:
            sub_pct = sub_monthly_total / (annual_income / 12) * 100
            if sub_pct > 10:
                weaknesses.append(
                    f"Subscription costs (₹{sub_monthly_total:,.0f}/month) consume {sub_pct:.1f}% of monthly income. Review and cancel unused subscriptions."
                )

        # Top category
        if top_category and top_category != "N/A":
            weaknesses.append(
                f"{top_category} is your highest expense category. Review if this aligns with your FIRE goals."
            )

        # Goals
        if goal_progress_avg >= 60:
            strengths.append(f"Good goal achievement rate of {goal_progress_avg:.0f}% average across active goals.")

        # Ensure at least one of each
        if not strengths:
            strengths.append("You have taken the first step by tracking your finances — consistency is key to FIRE.")
        if not weaknesses:
            weaknesses.append("Keep monitoring your FIRE score monthly to stay on track.")

        return strengths[:6], weaknesses[:6]

    # ─────────────────────────────────────────────────────────────────────
    # Status label
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def _status_label(
        estimated_fire_age: float,
        retirement_target_age: int,
        fire_progress: float,
    ) -> str:
        if fire_progress >= 100:
            return "🏁 FIRE Achieved!"
        gap = estimated_fire_age - retirement_target_age
        if gap <= 0:
            return "🟢 On Track"
        elif gap <= 5:
            return "🟡 Slightly Behind"
        elif gap <= 10:
            return "🟠 Behind Schedule"
        else:
            return "🔴 Critical — Action Needed"

    # ─────────────────────────────────────────────────────────────────────
    # Hydrate result from stored DB record
    # ─────────────────────────────────────────────────────────────────────

    def _hydrate_from_db(self, record: FireAnalysis) -> FireCalculationResult:
        """Reconstruct a FireCalculationResult from a stored FireAnalysis row."""
        settings = FireSettings(
            current_age=record.current_age,
            retirement_target_age=record.retirement_target_age,
            investment_return=record.investment_return,
            inflation_rate=record.inflation_rate,
            lifestyle=record.lifestyle,  # type: ignore[arg-type]
        )

        projection_raw = record.wealth_projection or []
        projection = [WealthProjectionPoint(**p) for p in projection_raw]

        scenarios_raw = record.scenarios or []
        scenarios = [FireScenario(**s) for s in scenarios_raw]

        # Rebuild score breakdown from stored score (approximation for display)
        score_breakdown = FireScoreBreakdown(
            savings_rate_score=0.0,
            health_score_contribution=0.0,
            debt_ratio_score=0.0,
            net_worth_growth_score=0.0,
            investment_discipline_score=0.0,
            budget_discipline_score=0.0,
        )

        monthly_income = record.annual_income / 12
        monthly_expenses = record.annual_expenses / 12

        status_label = self._status_label(
            estimated_fire_age=record.estimated_fire_age,
            retirement_target_age=record.retirement_target_age,
            fire_progress=record.fire_progress,
        )

        return FireCalculationResult(
            settings=settings,
            current_net_worth=record.current_net_worth,
            total_assets=0.0,
            total_liabilities=0.0,
            annual_income=record.annual_income,
            annual_expenses=record.annual_expenses,
            annual_savings=record.annual_savings,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            monthly_savings=monthly_income - monthly_expenses,
            savings_rate=record.savings_rate,
            debt_ratio=0.0,
            financial_health_score=0.0,
            fire_target_corpus=record.fire_target_corpus,
            fire_progress=record.fire_progress,
            fire_score=record.fire_score,
            score_breakdown=score_breakdown,
            estimated_fire_age=record.estimated_fire_age,
            years_remaining=record.years_remaining,
            required_monthly_investment=record.required_monthly_investment,
            wealth_projection=projection,
            scenarios=scenarios,
            strengths=record.strengths or [],
            weaknesses=record.weaknesses or [],
            subscription_monthly_total=0.0,
            goal_progress_avg=0.0,
            top_expense_category="N/A",
            status_label=status_label,
        )

    @staticmethod
    def _result_to_context(result: FireCalculationResult) -> dict:
        return {
            "current_age": result.settings.current_age,
            "retirement_target_age": result.settings.retirement_target_age,
            "current_net_worth": round(result.current_net_worth, 2),
            "annual_income": round(result.annual_income, 2),
            "annual_expenses": round(result.annual_expenses, 2),
            "savings_rate_percent": round(result.savings_rate, 1),
            "fire_score": round(result.fire_score, 1),
            "fire_progress_percent": round(result.fire_progress, 1),
            "fire_target_corpus": round(result.fire_target_corpus, 2),
            "estimated_fire_age": round(result.estimated_fire_age, 1),
            "years_remaining": round(result.years_remaining, 1),
            "required_monthly_investment": round(result.required_monthly_investment, 2),
            "lifestyle": result.settings.lifestyle,
            "strengths": result.strengths[:3],
            "weaknesses": result.weaknesses[:3],
        }
