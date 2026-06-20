"""
Wallet Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.models import Wallet, Transaction
from sqlalchemy import func

wallets_bp = Blueprint('wallets', __name__, url_prefix='/wallets')

WALLET_TYPES = ['bank', 'credit_card', 'cash', 'digital', 'investment']
WALLET_COLORS = ['#6c63ff', '#00d4a8', '#ff4757', '#ffa502', '#2ed573', '#1e90ff', '#ff6b81', '#eccc68']


@wallets_bp.route('/')
def index():
    wallets = Wallet.query.filter_by(is_active=True).all()
    wallet_stats = []
    for w in wallets:
        txn_count = Transaction.query.filter_by(wallet_id=w.id, is_duplicate=False).count()
        total_credits = db.session.query(func.sum(Transaction.amount)).filter_by(
            wallet_id=w.id, type='credit', is_duplicate=False
        ).scalar() or 0
        total_debits = db.session.query(func.sum(Transaction.amount)).filter_by(
            wallet_id=w.id, type='debit', is_duplicate=False
        ).scalar() or 0
        wallet_stats.append({
            'wallet': w,
            'txn_count': txn_count,
            'total_credits': float(total_credits),
            'total_debits': float(total_debits),
        })

    total_balance = sum(float(w.balance) for w in wallets)
    return render_template('wallets.html', wallet_stats=wallet_stats,
                           total_balance=total_balance, wallet_types=WALLET_TYPES, colors=WALLET_COLORS)


@wallets_bp.route('/add', methods=['POST'])
def add():
    try:
        wallet = Wallet(
            name=request.form['name'].strip(),
            type=request.form.get('type', 'bank'),
            balance=float(request.form.get('balance', 0)),
            currency=request.form.get('currency', 'INR'),
            institution=request.form.get('institution', '').strip() or None,
            account_number=request.form.get('account_number', '').strip() or None,
            color=request.form.get('color', '#6c63ff'),
        )
        db.session.add(wallet)
        db.session.commit()
        flash(f'Wallet "{wallet.name}" added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding wallet: {str(e)}', 'error')
    return redirect(url_for('wallets.index'))


@wallets_bp.route('/<int:wallet_id>/edit', methods=['POST'])
def edit(wallet_id):
    wallet = Wallet.query.get_or_404(wallet_id)
    try:
        wallet.name = request.form['name'].strip()
        wallet.type = request.form.get('type', wallet.type)
        wallet.balance = float(request.form.get('balance', wallet.balance))
        wallet.institution = request.form.get('institution', '').strip() or None
        wallet.color = request.form.get('color', wallet.color)
        db.session.commit()
        flash('Wallet updated!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating wallet: {str(e)}', 'error')
    return redirect(url_for('wallets.index'))


@wallets_bp.route('/<int:wallet_id>/delete', methods=['POST'])
def delete(wallet_id):
    wallet = Wallet.query.get_or_404(wallet_id)
    wallet.is_active = False
    db.session.commit()
    return jsonify({'success': True})
