"""
Subscription Detector
Identifies recurring payments from transaction history.
"""
from datetime import date, timedelta
from collections import defaultdict
from typing import List, Dict
from app.extensions import db
from app.models import Transaction, Subscription, Merchant


def detect_subscriptions() -> List[Dict]:
    """
    Detect recurring payments from transaction history.
    Returns a list of detected subscription patterns.
    """
    # Fetch all debit transactions from last 6 months
    six_months_ago = date.today() - timedelta(days=180)
    transactions = Transaction.query.filter(
        Transaction.date >= six_months_ago,
        Transaction.type == 'debit',
        Transaction.is_duplicate == False,
    ).order_by(Transaction.date).all()

    # Group by merchant name + amount (rounded)
    groups = defaultdict(list)
    for txn in transactions:
        key = (txn.merchant_name_raw or txn.description[:30], round(float(txn.amount), 0))
        groups[key].append(txn)

    detected = []
    for (merchant_name, amount), txns in groups.items():
        if len(txns) < 2:
            continue

        # Check if dates are roughly periodic
        dates = sorted([t.date for t in txns])
        gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]

        if not gaps:
            continue

        avg_gap = sum(gaps) / len(gaps)

        # Classify frequency
        if 25 <= avg_gap <= 35:
            frequency = 'monthly'
        elif 6 <= avg_gap <= 8:
            frequency = 'weekly'
        elif 85 <= avg_gap <= 95:
            frequency = 'quarterly'
        elif 355 <= avg_gap <= 375:
            frequency = 'yearly'
        else:
            continue  # Not regular enough

        last_date = dates[-1]
        next_expected = last_date + timedelta(days=round(avg_gap))

        detected.append({
            'name': merchant_name,
            'amount': amount,
            'frequency': frequency,
            'last_detected': last_date.isoformat(),
            'next_expected': next_expected.isoformat(),
            'occurrences': len(txns),
        })

    return detected


def sync_subscriptions():
    """Sync detected subscriptions to the database."""
    detected = detect_subscriptions()

    for sub_data in detected:
        # Check if already exists
        existing = Subscription.query.filter_by(
            name=sub_data['name'],
            frequency=sub_data['frequency'],
        ).first()

        if existing:
            existing.amount = sub_data['amount']
            existing.last_detected = date.fromisoformat(sub_data['last_detected'])
            existing.next_expected = date.fromisoformat(sub_data['next_expected'])
        else:
            new_sub = Subscription(
                name=sub_data['name'],
                amount=sub_data['amount'],
                frequency=sub_data['frequency'],
                last_detected=date.fromisoformat(sub_data['last_detected']),
                next_expected=date.fromisoformat(sub_data['next_expected']),
                is_active=True,
            )
            db.session.add(new_sub)

    db.session.commit()
    return detected
