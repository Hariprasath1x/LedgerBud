"""
Dashboard Routes
"""
from flask import Blueprint, render_template
from datetime import date
from app.models import Wallet, Transaction
from app.intelligence import (
    get_monthly_summary, get_category_breakdown,
    calculate_health_score, generate_insights,
    get_monthly_trends, get_top_merchants
)
from app.extensions import db
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def index():
    today = date.today()
    year, month = today.year, today.month

    # Wallet summary
    wallets = Wallet.query.filter_by(is_active=True).all()
    total_balance = sum(float(w.balance) for w in wallets)

    # Monthly summary
    summary = get_monthly_summary(year, month)

    # Category breakdown
    categories = get_category_breakdown(year, month)

    # Health score
    health = calculate_health_score(year, month)

    # Monthly trends (6 months)
    trends = get_monthly_trends(6)

    # Top merchants this month
    top_merchants = get_top_merchants(5)

    # Recent transactions
    recent_transactions = Transaction.query.filter_by(
        is_duplicate=False
    ).order_by(Transaction.date.desc(), Transaction.id.desc()).limit(8).all()

    # Insights
    insights = generate_insights(year, month)

    return render_template(
        'dashboard.html',
        wallets=wallets,
        total_balance=total_balance,
        summary=summary,
        categories=categories,
        health=health,
        trends=trends,
        top_merchants=top_merchants,
        recent_transactions=recent_transactions,
        insights=insights,
        current_month=today.strftime('%B %Y'),
    )
