"""
Duplicate Detector
Identifies duplicate transactions based on date + amount + description similarity.
"""
import logging
from datetime import date
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NormalizedTransaction:
    """A partially normalized transaction ready for deduplication."""
    date: Optional[date]
    description: str
    amount: Decimal
    type: str  # debit / credit
    balance_after: Optional[Decimal]
    reference_no: Optional[str]
    merchant_name_raw: str
    raw_date_str: str


def detect_duplicates(
    new_transactions: List[NormalizedTransaction],
    existing_transactions: List[Dict]
) -> Tuple[List[NormalizedTransaction], List[NormalizedTransaction]]:
    """
    Split new_transactions into (unique, duplicates).
    Checks against existing DB records and within the new batch itself.
    """
    unique = []
    duplicates = []
    seen_fingerprints = set()

    # Build fingerprints from existing transactions
    for txn in existing_transactions:
        fp = _fingerprint(txn.get('date'), txn.get('amount'), txn.get('description', ''))
        seen_fingerprints.add(fp)

    for txn in new_transactions:
        fp = _fingerprint(
            txn.date.isoformat() if txn.date else '',
            str(txn.amount),
            txn.description,
        )

        if fp in seen_fingerprints:
            duplicates.append(txn)
        else:
            unique.append(txn)
            seen_fingerprints.add(fp)  # Prevent within-batch duplicates too

    return unique, duplicates


def _fingerprint(date_str: str, amount_str: str, description: str) -> str:
    """Create a deduplication fingerprint."""
    # Normalize amount
    try:
        amount = round(float(str(amount_str).replace(',', '')), 2)
    except (ValueError, TypeError):
        amount = 0.0

    # Normalize description to first 30 chars (handles minor variations)
    desc_key = description.lower().strip()[:30]

    return f'{date_str}|{amount}|{desc_key}'
