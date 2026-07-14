"""AI Financial Advisor.

Generates data-specific advice from summarized financial context and optionally
uses Groq for conversational responses. It never sends raw transaction rows.
"""

from __future__ import annotations

import json
import os
from datetime import date
from typing import Dict, List, Optional

from app.extensions import db
from app.intelligence.health_score import calculate_health_score
from app.intelligence.net_worth import get_net_worth_summary
from app.intelligence.spending_insights import (
    get_category_breakdown,
    get_monthly_summary,
    get_monthly_trends,
)
from app.models import AdvisorConversation, AdvisorMessage, Budget, Goal, Subscription

try:  # Optional dependency. The app still works without it.
    from groq import Groq  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    Groq = None


def get_advisor_context() -> Dict:
    """Build a summarized, privacy-safe financial context for the advisor."""
    today = date.today()
    year, month = today.year, today.month

    summary = get_monthly_summary(year, month)
    categories = get_category_breakdown(year, month)
    trends = get_monthly_trends(months=3)
    health = calculate_health_score(year, month)
    net_worth = get_net_worth_summary()

    goals = Goal.query.filter(Goal.status.in_(['active', 'paused'])).all()
    budgets = Budget.query.filter_by(is_active=True).all()
    subscriptions = Subscription.query.filter_by(is_active=True).all()

    active_goal_amount = sum(float(goal.current_amount) for goal in goals if goal.status == 'active')
    active_goal_target = sum(float(goal.target_amount) for goal in goals if goal.status == 'active')
    sub_total = sum(float(subscription.amount) for subscription in subscriptions)

    return {
        'summary': summary,
        'categories': categories[:5],
        'trends': trends,
        'health': health,
        'net_worth': net_worth,
        'active_goals': len([goal for goal in goals if goal.status == 'active']),
        'goal_completion_rate': round((active_goal_amount / active_goal_target * 100), 1) if active_goal_target > 0 else 0,
        'active_budgets': len(budgets),
        'subscription_total': sub_total,
        'subscription_count': len(subscriptions),
    }


def generate_advice() -> List[Dict]:
    """Generate a list of precise, data-backed advice cards."""
    advice_list: List[Dict] = []
    ctx = get_advisor_context()

    summary = ctx['summary']
    categories = ctx['categories']
    trends = ctx['trends']
    net_worth = ctx['net_worth']

    income = summary.get('income', 0)
    expense = summary.get('expense', 0)
    savings = summary.get('savings', 0)
    savings_rate = summary.get('savings_rate', 0)
    sub_total = ctx['subscription_total']
    net_worth_value = net_worth.get('net_worth', 0)

    if savings > 0 and income > 0:
        emergency_target = income * 6
        advice_list.append({
            'category': 'Emergency Fund',
            'priority': 'high',
            'icon': 'shield',
            'title': 'Build Your Emergency Fund',
            'message': (
                f'Aim for ₹{emergency_target:,.0f} as a 6-month cushion. '
                f'You are currently saving ₹{savings:,.0f}/month, so at the current rate you would reach it in '
                f'{max(1, round(emergency_target / max(savings, 1)))} months.'
            ),
            'action': 'Create an Emergency Fund Goal',
        })

    if sub_total > 0:
        advice_list.append({
            'category': 'Subscriptions',
            'priority': 'medium',
            'icon': 'repeat',
            'title': f'Review Your ₹{sub_total:,.0f}/mo in Subscriptions',
            'message': f'You have {ctx["subscription_count"]} active subscriptions totaling ₹{sub_total:,.0f}/month. '
                       f'That is ₹{sub_total * 12:,.0f}/year in recurring commitments.',
            'action': 'View Subscriptions',
        })

    if ctx['active_budgets'] == 0 and expense > 0:
        advice_list.append({
            'category': 'Budgets',
            'priority': 'high',
            'icon': 'sliders',
            'title': 'Set Up Category Budgets',
            'message': 'You are spending, but no budgets are active yet. Budget limits make overspending obvious before month-end.',
            'action': 'Create Budgets',
        })

    if ctx['active_goals'] == 0:
        advice_list.append({
            'category': 'Goals',
            'priority': 'medium',
            'icon': 'target',
            'title': 'Set a Concrete Savings Goal',
            'message': 'Goals make savings measurable. Pick one target with a deadline so your monthly surplus has a destination.',
            'action': 'Create a Goal',
        })
    elif ctx['goal_completion_rate'] > 0:
        advice_list.append({
            'category': 'Goals',
            'priority': 'low',
            'icon': 'award',
            'title': f'Your goals are {ctx["goal_completion_rate"]}% funded',
            'message': 'You already have savings momentum. Rebalance contributions toward the closest-due goal first to finish one faster.',
            'action': 'Review Goals',
        })

    if savings_rate >= 20:
        advice_list.append({
            'category': 'Investing',
            'priority': 'low',
            'icon': 'trending-up',
            'title': 'Put Part of Your Savings to Work',
            'message': f'You are saving ₹{savings:,.0f}/month and your net worth is ₹{net_worth_value:,.0f}. '
                       f'If you invest a disciplined portion of the surplus, compounding can accelerate your wealth plan.',
            'action': 'Explore Investments',
        })

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
                    'message': f'Your expenses rose from ₹{prev_expense:,.0f} to ₹{curr_expense:,.0f}. This is a concrete change worth investigating.',
                    'action': 'View Transactions',
                })

    return advice_list


def get_or_create_conversation(session_id: str) -> AdvisorConversation:
    conversation = AdvisorConversation.query.filter_by(session_id=session_id).first()
    if conversation:
        return conversation

    conversation = AdvisorConversation(session_id=session_id, title='Financial Advisor')
    db.session.add(conversation)
    db.session.commit()
    return conversation


def get_conversation_messages(session_id: str) -> List[Dict]:
    conversation = AdvisorConversation.query.filter_by(session_id=session_id).first()
    if not conversation:
        return []
    return [message.to_dict() for message in conversation.messages.order_by(AdvisorMessage.created_at.asc()).all()]


def store_conversation_message(session_id: str, role: str, content: str) -> Dict:
    conversation = get_or_create_conversation(session_id)
    message = AdvisorMessage(conversation_id=conversation.id, role=role, content=content)
    db.session.add(message)
    db.session.commit()
    return message.to_dict()


def clear_conversation(session_id: str) -> None:
    conversation = AdvisorConversation.query.filter_by(session_id=session_id).first()
    if not conversation:
        return
    db.session.delete(conversation)
    db.session.commit()


def _build_prompt(question: str, context: Dict, history: Optional[List[Dict]] = None) -> str:
    history_text = ''
    if history:
        snippets = [f"{item['role']}: {item['content']}" for item in history[-6:]]
        history_text = '\n'.join(snippets)

    return f"""
You are LedgerBud's financial advisor.
Use only the provided summarized financial context. Never be generic.
Answer with exact figures where possible and refer to the user's actual spending, goals, net worth, subscriptions, and health score.
If the data is insufficient, say exactly what is missing.

Financial context JSON:
{json.dumps(context, indent=2, default=str)}

Recent conversation:
{history_text or 'No prior messages.'}

User question:
{question}

Return a concise answer with 3 short bullets max and one direct recommendation.
""".strip()


def _fallback_answer(question: str, context: Dict) -> str:
    summary = context['summary']
    net_worth = context['net_worth']
    health = context['health']
    categories = context['categories']

    top_category = categories[0]['category'] if categories else 'uncategorized spending'
    top_spend = categories[0]['amount'] if categories else 0

    question_lower = question.lower()
    if 'save' in question_lower:
        return (
            f"You are saving ₹{summary['savings']:,.0f}/month at a {summary['savings_rate']:.1f}% savings rate. "
            f"Your fastest lever is {top_category}, which is consuming ₹{top_spend:,.0f} this month. "
            f"Reduce that category by 10-15% and move the difference into your emergency fund goal."
        )
    if 'category' in question_lower or 'reduce' in question_lower:
        return (
            f"Reduce {top_category} first. It is your highest spending category at ₹{top_spend:,.0f} and your current health score is {health['score']}. "
            f"That single adjustment will have more impact than trimming low-value minor expenses."
        )
    if 'goal' in question_lower:
        return (
            f"Your current net worth is ₹{net_worth['net_worth']:,.0f}. The best next goal is the one closest to completion, because your current savings can compound into a visible win faster. "
            f"Focus on one active goal and fund it from your monthly surplus of ₹{summary['savings']:,.0f}."
        )

    return (
        f"Your net worth is ₹{net_worth['net_worth']:,.0f}, savings rate is {summary['savings_rate']:.1f}%, and health score is {health['score']}. "
        f"The biggest pressure point is {top_category}. If you want the fastest improvement, reduce that category and direct the savings to a goal or cash reserve."
    )


def generate_chat_response(question: str, history: Optional[List[Dict]] = None) -> Dict:
    """Generate a precise advisor reply from summarized user data."""
    context = get_advisor_context()
    prompt = _build_prompt(question, context, history)

    groq_key = os.environ.get('GROQ_API_KEY', '').strip()
    groq_model = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')

    if groq_key and Groq is not None:
        try:
            client = Groq(api_key=groq_key)
            completion = client.chat.completions.create(
                model=groq_model,
                messages=[
                    {'role': 'system', 'content': 'You are LedgerBud, a precise personal finance advisor.'},
                    {'role': 'user', 'content': prompt},
                ],
                temperature=0.2,
            )
            answer = completion.choices[0].message.content.strip()
            return {
                'provider': 'groq',
                'model': groq_model,
                'answer': answer,
                'context': context,
            }
        except Exception:
            pass

    answer = _fallback_answer(question, context)
    return {
        'provider': 'fallback',
        'model': None,
        'answer': answer,
        'context': context,
    }
