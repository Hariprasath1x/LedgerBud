"""
Budget Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import date, timedelta
from app.extensions import db
from app.models import Budget, Category, Transaction
from sqlalchemy import func

budgets_bp = Blueprint('budgets', __name__, url_prefix='/budgets')


def _get_budget_usage(budget: Budget) -> dict:
    """Calculate how much of a budget has been spent this period."""
    today = date.today()
    start = date(today.year, today.month, 1)
    if today.month == 12:
        end = date(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(today.year, today.month + 1, 1) - timedelta(days=1)

    spent = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.category_id == budget.category_id,
        Transaction.date >= start,
        Transaction.date <= end,
        Transaction.type == 'debit',
        Transaction.is_duplicate == False,
    ).scalar() or 0

    spent = float(spent)
    limit = float(budget.amount)
    percentage = min(100.0, (spent / limit * 100)) if limit > 0 else 0

    return {
        'spent': spent,
        'limit': limit,
        'remaining': max(0, limit - spent),
        'percentage': round(percentage, 1),
        'is_exceeded': spent > limit,
    }


@budgets_bp.route('/')
def index():
    budgets = Budget.query.filter_by(is_active=True).all()
    budget_data = []
    for b in budgets:
        usage = _get_budget_usage(b)
        budget_data.append({'budget': b, 'usage': usage})

    # Sort by percentage used (highest first)
    budget_data.sort(key=lambda x: x['usage']['percentage'], reverse=True)

    categories = Category.query.filter_by(type='expense').order_by(Category.name).all()
    today = date.today()

    return render_template('budgets.html', budget_data=budget_data, categories=categories,
                           current_month=today.strftime('%B %Y'))


@budgets_bp.route('/add', methods=['POST'])
def add():
    try:
        today = date.today()
        budget = Budget(
            name=request.form['name'].strip(),
            category_id=int(request.form['category_id']),
            amount=float(request.form['amount']),
            period=request.form.get('period', 'monthly'),
            start_date=date(today.year, today.month, 1),
        )
        db.session.add(budget)
        db.session.commit()
        flash(f'Budget "{budget.name}" created!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating budget: {str(e)}', 'error')
    return redirect(url_for('budgets.index'))


@budgets_bp.route('/<int:budget_id>/edit', methods=['POST'])
def edit(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    try:
        budget.name = request.form['name'].strip()
        budget.amount = float(request.form['amount'])
        budget.category_id = int(request.form['category_id'])
        db.session.commit()
        flash('Budget updated!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('budgets.index'))


@budgets_bp.route('/<int:budget_id>/delete', methods=['POST'])
def delete(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    budget.is_active = False
    db.session.commit()
    return jsonify({'success': True})


@budgets_bp.route('/api/status')
def api_status():
    """JSON: current budget status for all budgets."""
    budgets = Budget.query.filter_by(is_active=True).all()
    result = []
    for b in budgets:
        usage = _get_budget_usage(b)
        data = b.to_dict()
        data.update(usage)
        result.append(data)
    return jsonify(result)
