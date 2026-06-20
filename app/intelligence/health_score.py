"""
Financial Health Score (0-100)
Calculates a composite score based on:
- Savings rate (40 points)
- Budget adherence (30 points)
- Expense diversity (15 points)
- Goal progress (15 points)
"""
from datetime import date, timedelta
from app.extensions import db
from app.models import Transaction, Budget, Goal
from app.intelligence.spending_insights import get_monthly_summary, get_category_breakdown
from sqlalchemy import func


def calculate_health_score(year: int = None, month: int = None) -> dict:
    """Calculate the overall Financial Health Score."""
    today = date.today()
    year = year or today.year
    month = month or today.month

    summary = get_monthly_summary(year, month)
    categories = get_category_breakdown(year, month)

    # 1. Savings Score (40 points max)
    savings_rate = summary.get('savings_rate', 0)
    if savings_rate >= 30:
        savings_score = 40
    elif savings_rate >= 20:
        savings_score = 30
    elif savings_rate >= 10:
        savings_score = 20
    elif savings_rate >= 0:
        savings_score = 10
    else:
        savings_score = 0

    # 2. Budget Adherence Score (30 points max)
    budget_score = _calculate_budget_score(year, month)

    # 3. Expense Diversity Score (15 points max)
    # Penalize if any single category > 50%
    diversity_score = 15
    if categories:
        top_pct = categories[0]['percentage']
        if top_pct > 70:
            diversity_score = 5
        elif top_pct > 50:
            diversity_score = 10

    # 4. Goal Progress Score (15 points max)
    goal_score = _calculate_goal_score()

    total = savings_score + budget_score + diversity_score + goal_score
    total = max(0, min(100, total))

    # Grade
    if total >= 80:
        grade, label = 'A', 'Excellent'
    elif total >= 65:
        grade, label = 'B', 'Good'
    elif total >= 50:
        grade, label = 'C', 'Fair'
    elif total >= 35:
        grade, label = 'D', 'Needs Attention'
    else:
        grade, label = 'F', 'Poor'

    return {
        'score': total,
        'grade': grade,
        'label': label,
        'breakdown': {
            'savings': savings_score,
            'budgets': budget_score,
            'diversity': diversity_score,
            'goals': goal_score,
        },
        'savings_rate': savings_rate,
    }


def _calculate_budget_score(year: int, month: int) -> int:
    """Calculate budget adherence score (0-30)."""
    budgets = Budget.query.filter_by(is_active=True).all()
    if not budgets:
        return 15  # Default if no budgets set

    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)

    within_budget = 0
    for budget in budgets:
        spent = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.category_id == budget.category_id,
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.type == 'debit',
            Transaction.is_duplicate == False,
        ).scalar() or 0

        if float(spent) <= float(budget.amount):
            within_budget += 1

    ratio = within_budget / len(budgets) if budgets else 1.0
    return round(ratio * 30)


def _calculate_goal_score() -> int:
    """Calculate goal progress score (0-15)."""
    goals = Goal.query.filter_by(status='active').all()
    if not goals:
        return 10  # Default if no goals

    avg_progress = sum(g.progress_percentage for g in goals) / len(goals)
    return round(avg_progress / 100 * 15)
