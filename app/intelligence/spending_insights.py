"""
Spending Insights Engine
Generates personalized spending insights from transaction data.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict
from sqlalchemy import func
from app.extensions import db
from app.models import Transaction, Category


def get_monthly_summary(year: int, month: int) -> Dict:
    """Get income vs expense summary for a given month."""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)

    result = db.session.query(
        Transaction.type,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.date >= start,
        Transaction.date <= end,
        Transaction.is_duplicate == False
    ).group_by(Transaction.type).all()

    income = 0.0
    expense = 0.0
    for row in result:
        if row.type == 'credit':
            income = float(row.total or 0)
        elif row.type == 'debit':
            expense = float(row.total or 0)

    return {
        'income': income,
        'expense': expense,
        'savings': income - expense,
        'savings_rate': round((income - expense) / income * 100, 1) if income > 0 else 0,
        'month': f'{year}-{month:02d}',
    }


def get_category_breakdown(year: int, month: int) -> List[Dict]:
    """Get spending breakdown by category for a given month."""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)

    results = db.session.query(
        Category.name,
        Category.color,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.id).label('count'),
    ).join(Transaction, Transaction.category_id == Category.id).filter(
        Transaction.date >= start,
        Transaction.date <= end,
        Transaction.type == 'debit',
        Transaction.is_duplicate == False,
    ).group_by(Category.name, Category.color).order_by(
        func.sum(Transaction.amount).desc()
    ).all()

    total_expense = sum(float(r.total or 0) for r in results)

    return [
        {
            'category': r.name,
            'color': r.color,
            'amount': float(r.total or 0),
            'count': r.count,
            'percentage': round(float(r.total or 0) / total_expense * 100, 1) if total_expense > 0 else 0,
        }
        for r in results
    ]


def get_monthly_trends(months: int = 6) -> List[Dict]:
    """Get income/expense trend for the last N months."""
    trends = []
    today = date.today()

    for i in range(months - 1, -1, -1):
        if today.month - i <= 0:
            year = today.year - 1
            month = 12 + (today.month - i)
        else:
            year = today.year
            month = today.month - i

        summary = get_monthly_summary(year, month)
        trends.append(summary)

    return trends


def get_top_merchants(limit: int = 10, month: int = None, year: int = None) -> List[Dict]:
    """Get top spending merchants."""
    from app.models import Merchant
    today = date.today()
    month = month or today.month
    year = year or today.year

    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)

    results = db.session.query(
        Transaction.merchant_name_raw,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.id).label('count'),
    ).filter(
        Transaction.date >= start,
        Transaction.date <= end,
        Transaction.type == 'debit',
        Transaction.is_duplicate == False,
    ).group_by(Transaction.merchant_name_raw).order_by(
        func.sum(Transaction.amount).desc()
    ).limit(limit).all()

    return [
        {
            'merchant': r.merchant_name_raw or 'Unknown',
            'amount': float(r.total or 0),
            'count': r.count,
        }
        for r in results
    ]


def generate_insights(year: int, month: int) -> List[Dict]:
    """Generate AI-like rule-based spending insights."""
    insights = []
    summary = get_monthly_summary(year, month)
    categories = get_category_breakdown(year, month)

    if summary['savings_rate'] < 20 and summary['income'] > 0:
        insights.append({
            'type': 'warning',
            'icon': 'alert-triangle',
            'title': 'Low Savings Rate',
            'message': f"You're saving only {summary['savings_rate']:.1f}% of your income this month. Aim for at least 20%.",
        })
    elif summary['savings_rate'] >= 30:
        insights.append({
            'type': 'success',
            'icon': 'check-circle',
            'title': 'Great Savings!',
            'message': f"You're saving {summary['savings_rate']:.1f}% of your income. Keep it up!",
        })

    # Top category insight
    if categories:
        top = categories[0]
        if top['percentage'] > 40:
            insights.append({
                'type': 'info',
                'icon': 'pie-chart',
                'title': f"{top['category']} is Dominant",
                'message': f"{top['category']} makes up {top['percentage']:.1f}% of your spending. Consider if this aligns with your priorities.",
            })

    # Food spending
    food_cats = [c for c in categories if c['category'].lower() in ['food & dining', 'food', 'dining', 'groceries']]
    food_total = sum(c['amount'] for c in food_cats)
    if food_total > 0 and summary['income'] > 0 and food_total / summary['income'] > 0.30:
        insights.append({
            'type': 'warning',
            'icon': 'utensils',
            'title': 'High Food Spending',
            'message': f'Food & dining accounts for {food_total / summary["income"] * 100:.1f}% of your income. Consider meal planning or cooking at home.',
        })

    return insights
