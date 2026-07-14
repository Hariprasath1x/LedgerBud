"""
Analytics Routes
"""
from flask import Blueprint, render_template, jsonify, request, session
from datetime import date
from app.intelligence import (
    get_monthly_summary, get_category_breakdown, get_monthly_trends,
    generate_insights, calculate_health_score, detect_subscriptions,
    generate_advice, get_net_worth_summary, get_conversation_messages,
    get_or_create_conversation, generate_chat_response, store_conversation_message,
    clear_conversation,
)
from app.intelligence.spending_insights import get_top_merchants
from app.models import Subscription
import uuid

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/')
def index():
    today = date.today()
    year, month = today.year, today.month

    summary = get_monthly_summary(year, month)
    categories = get_category_breakdown(year, month)
    trends = get_monthly_trends(6)
    health = calculate_health_score(year, month)
    top_merchants = get_top_merchants(10)
    insights = generate_insights(year, month)
    advice = generate_advice()
    net_worth = get_net_worth_summary()

    session_id = session.get('advisor_session_id')
    if not session_id:
        session_id = uuid.uuid4().hex
        session['advisor_session_id'] = session_id
    get_or_create_conversation(session_id)
    advisor_messages = get_conversation_messages(session_id)

    # Subscriptions
    subscriptions = Subscription.query.filter_by(is_active=True).all()
    sub_detected = detect_subscriptions()

    return render_template(
        'analytics.html',
        summary=summary,
        categories=categories,
        trends=trends,
        health=health,
        top_merchants=top_merchants,
        insights=insights,
        advice=advice,
        net_worth=net_worth,
        advisor_messages=advisor_messages,
        subscriptions=subscriptions,
        sub_detected=sub_detected,
        current_month=today.strftime('%B %Y'),
    )


@analytics_bp.route('/api/trends')
def api_trends():
    months = request.args.get('months', 6, type=int)
    trends = get_monthly_trends(months)
    return jsonify(trends)


@analytics_bp.route('/api/categories')
def api_categories():
    today = date.today()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    categories = get_category_breakdown(year, month)
    return jsonify(categories)


@analytics_bp.route('/api/summary')
def api_summary():
    today = date.today()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    return jsonify(get_monthly_summary(year, month))


@analytics_bp.route('/api/whatif')
def api_whatif():
    """What-If analysis: simulate reducing a category spend."""
    today = date.today()
    category = request.args.get('category', '')
    reduce_by = request.args.get('reduce_by', 0, type=float)

    summary = get_monthly_summary(today.year, today.month)
    new_expense = max(0, summary['expense'] - reduce_by)
    new_savings = summary['income'] - new_expense
    new_savings_rate = (new_savings / summary['income'] * 100) if summary['income'] > 0 else 0

    yearly_savings = new_savings * 12
    # Simple compound interest projection: 10 years at 12% p.a.
    investment_value = yearly_savings * ((1.12 ** 10 - 1) / 0.12) if yearly_savings > 0 else 0

    return jsonify({
        'current_expense': summary['expense'],
        'new_expense': new_expense,
        'current_savings': summary['savings'],
        'new_savings': new_savings,
        'new_savings_rate': round(new_savings_rate, 1),
        'yearly_savings': yearly_savings,
        'investment_value_10yr': round(investment_value, 0),
        'reduction': reduce_by,
    })


@analytics_bp.route('/api/advisor/chat', methods=['POST'])
def api_advisor_chat():
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get('question') or '').strip()
    if not question:
        return jsonify({'success': False, 'error': 'Question is required'}), 400

    session_id = session.get('advisor_session_id')
    if not session_id:
        session_id = uuid.uuid4().hex
        session['advisor_session_id'] = session_id

    history = get_conversation_messages(session_id)
    store_conversation_message(session_id, 'user', question)
    result = generate_chat_response(question, history)
    assistant_message = store_conversation_message(session_id, 'assistant', result['answer'])

    return jsonify({
        'success': True,
        'provider': result['provider'],
        'answer': result['answer'],
        'assistant_message': assistant_message,
        'history': get_conversation_messages(session_id),
        'context': result['context'],
    })


@analytics_bp.route('/api/advisor/reset', methods=['POST'])
def api_advisor_reset():
    session_id = session.get('advisor_session_id')
    if session_id:
        clear_conversation(session_id)
    session.pop('advisor_session_id', None)
    return jsonify({'success': True})
