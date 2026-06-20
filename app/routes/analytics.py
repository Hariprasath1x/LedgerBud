"""
Analytics Routes
"""
from flask import Blueprint, render_template, jsonify, request
from datetime import date
from app.intelligence import (
    get_monthly_summary, get_category_breakdown, get_monthly_trends,
    generate_insights, calculate_health_score, detect_subscriptions,
    generate_advice
)
from app.intelligence.spending_insights import get_top_merchants
from app.models import Subscription

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
