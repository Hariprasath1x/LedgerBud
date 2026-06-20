"""
AI Financial Advisor
Generates personalized financial recommendations based on summarized financial context.
Operates on summaries, NOT raw transaction data (for privacy and performance).
"""
from datetime import date
from typing import List, Dict
from app.intelligence.spending_insights import get_monthly_summary, get_category_breakdown, get_monthly_trends
from app.intelligence.health_score import calculate_health_score
from app.models import Goal, Budget, Subscription


def get_advisor_context() -> Dict:
    """Build a financial summary context for the advisor."""
    today = date.today()
    year, month = today.year, today.month

    summary = get_monthly_summary(year, month)
    categories = get_category_breakdown(year, month)
    trends = get_monthly_trends(months=3)
    health = calculate_health_score(year, month)

    goals = Goal.query.filter_by(status='active').all()
    budgets = Budget.query.filter_by(is_active=True).all()
    subscriptions = Subscription.query.filter_by(is_active=True).all()

    sub_total = sum(float(s.amount) for s in subscriptions)

    return {
        'summary': summary,
        'categories': categories[:5],
        'trends': trends,
        'health': health,
        'active_goals': len(goals),
        'active_budgets': len(budgets),
        'subscription_total': sub_total,
        'subscription_count': len(subscriptions),
    }


def generate_advice() -> List[Dict]:
    """Generate a list of AI-style financial advice cards."""
    advice_list = []
    ctx = get_advisor_context()

    summary = ctx['summary']
    health = ctx['health']
    categories = ctx['categories']
    trends = ctx['trends']

    income = summary.get('income', 0)
    expense = summary.get('expense', 0)
    savings = summary.get('savings', 0)
    savings_rate = summary.get('savings_rate', 0)
    sub_total = ctx['subscription_total']

    # Advice 1: Emergency fund
    if savings > 0 and income > 0:
        emergency_target = income * 6
        advice_list.append({
            'category': 'Emergency Fund',
            'priority': 'high',
            'icon': 'shield',
            'title': 'Build Your Emergency Fund',
            'message': f'Aim to save ₹{emergency_target:,.0f} (6 months of income: ₹{income:,.0f}/mo) as an emergency cushion. '
                       f'You currently save ₹{savings:,.0f}/month. '
                       f'At this rate, you\'ll reach your target in {max(1, round(emergency_target / savings))} months.',
            'action': 'Create an Emergency Fund Goal',
        })

    # Advice 2: Subscription audit
    if sub_total > 0:
        advice_list.append({
            'category': 'Subscriptions',
            'priority': 'medium',
            'icon': 'repeat',
            'title': f'Review Your ₹{sub_total:,.0f}/mo in Subscriptions',
            'message': f'You have {ctx["subscription_count"]} active subscriptions totaling ₹{sub_total:,.0f}/month '
                       f'(₹{sub_total * 12:,.0f}/year). Review which ones you actually use.',
            'action': 'View Subscriptions',
        })

    # Advice 3: Budget setup
    if ctx['active_budgets'] == 0 and expense > 0:
        advice_list.append({
            'category': 'Budgets',
            'priority': 'high',
            'icon': 'sliders',
            'title': 'Set Up Category Budgets',
            'message': 'You haven\'t set any budgets yet. Setting spending limits by category is one of the most effective ways to control expenses.',
            'action': 'Create Budgets',
        })

    # Advice 4: Goals
    if ctx['active_goals'] == 0:
        advice_list.append({
            'category': 'Goals',
            'priority': 'medium',
            'icon': 'target',
            'title': 'Set a Savings Goal',
            'message': 'People who set specific financial goals save 2x more on average. '
                       'Try setting a goal for something meaningful — a vacation, gadget, or investment.',
            'action': 'Create a Goal',
        })

    # Advice 5: Investment
    if savings_rate >= 20:
        advice_list.append({
            'category': 'Investing',
            'priority': 'low',
            'icon': 'trending-up',
            'title': 'Put Your Savings to Work',
            'message': f'You\'re saving ₹{savings:,.0f}/month. Consider investing in a diversified mutual fund '
                       f'via SIP. ₹{round(savings * 0.7, 0):,.0f}/month invested at 12% p.a. could grow to '
                       f'₹{round(savings * 0.7 * 12 * 10 * 1.8, 0):,.0f} in 10 years.',
            'action': 'Explore Investments',
        })

    # Advice 6: Trending spend
    if len(trends) >= 2:
        prev_expense = trends[-2].get('expense', 0)
        curr_expense = trends[-1].get('expense', 0)
        if curr_expense > 0 and prev_expense > 0:
            change = (curr_expense - prev_expense) / prev_expense * 100
            if change > 20:
                advice_list.append({
                    'category': 'Trend Alert',
                    'priority': 'high',
                    'icon': 'alert-triangle',
                    'title': f'Spending Up {change:.0f}% vs Last Month',
                    'message': f'Your expenses rose from ₹{prev_expense:,.0f} to ₹{curr_expense:,.0f} this month. '
                               f'Review your transactions to understand where the increase occurred.',
                    'action': 'View Transactions',
                })

    return advice_list
