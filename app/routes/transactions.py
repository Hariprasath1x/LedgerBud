"""
Transaction Routes
"""
import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import date, datetime
from app.extensions import db
from app.models import Transaction, Wallet, Category, Merchant

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@transactions_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Transaction.query.filter_by(is_duplicate=False)

    # Filters
    wallet_id = request.args.get('wallet_id', type=int)
    category_id = request.args.get('category_id', type=int)
    txn_type = request.args.get('type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search = request.args.get('search', '').strip()

    if wallet_id:
        query = query.filter_by(wallet_id=wallet_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if txn_type:
        query = query.filter_by(type=txn_type)
    if date_from:
        try:
            query = query.filter(Transaction.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Transaction.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
        except ValueError:
            pass
    if search:
        query = query.filter(Transaction.description.ilike(f'%{search}%'))

    transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    wallets = Wallet.query.filter_by(is_active=True).all()
    categories = Category.query.order_by(Category.name).all()

    return render_template(
        'transactions.html',
        transactions=transactions,
        wallets=wallets,
        categories=categories,
        filters={
            'wallet_id': wallet_id,
            'category_id': category_id,
            'type': txn_type,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }
    )


@transactions_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            wallet_id = request.form.get('wallet_id', type=int)
            category_id = request.form.get('category_id', type=int) or None
            txn_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            description = request.form['description'].strip()
            amount = float(request.form['amount'])
            txn_type = request.form.get('type', 'debit')
            notes = request.form.get('notes', '').strip()

            txn = Transaction(
                wallet_id=wallet_id,
                category_id=category_id,
                date=txn_date,
                description=description,
                merchant_name_raw=description,
                amount=amount,
                type=txn_type,
                notes=notes,
                is_manual=True,
            )
            db.session.add(txn)

            # Update wallet balance
            wallet = Wallet.query.get(wallet_id)
            if wallet:
                if txn_type == 'credit':
                    wallet.balance = float(wallet.balance) + amount
                else:
                    wallet.balance = float(wallet.balance) - amount

            db.session.commit()
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('transactions.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding transaction: {str(e)}', 'error')

    wallets = Wallet.query.filter_by(is_active=True).all()
    categories = Category.query.order_by(Category.name).all()
    return render_template('add_transaction.html', wallets=wallets, categories=categories)


@transactions_bp.route('/<int:txn_id>/update-category', methods=['POST'])
def update_category(txn_id):
    data = request.get_json()
    txn = Transaction.query.get_or_404(txn_id)
    txn.category_id = data.get('category_id')
    db.session.commit()
    return jsonify({'success': True})


@transactions_bp.route('/<int:txn_id>/delete', methods=['POST'])
def delete(txn_id):
    txn = Transaction.query.get_or_404(txn_id)
    db.session.delete(txn)
    db.session.commit()
    return jsonify({'success': True})


@transactions_bp.route('/api/list')
def api_list():
    """JSON endpoint for transaction data."""
    transactions = Transaction.query.filter_by(is_duplicate=False).order_by(
        Transaction.date.desc()
    ).limit(100).all()
    return jsonify([t.to_dict() for t in transactions])
