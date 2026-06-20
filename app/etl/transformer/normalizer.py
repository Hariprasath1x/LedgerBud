"""
Data Normalizer
Cleans and standardizes raw extracted transaction data:
- Date parsing & normalization
- Amount cleaning
- Description cleaning
"""
import re
import logging
from datetime import date
from typing import Optional
from decimal import Decimal, InvalidOperation
from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)

# Date formats commonly found in Indian bank statements
DATE_FORMATS = [
    '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y',
    '%d/%m/%y', '%d-%m-%y', '%d.%m.%y',
    '%d %b %Y', '%d %B %Y', '%d-%b-%Y', '%d-%b-%y',
    '%Y-%m-%d', '%Y/%m/%d',
    '%m/%d/%Y', '%m-%d-%Y',
]


def parse_date(date_str: str) -> Optional[date]:
    """Parse a date string into a Python date object."""
    if not date_str:
        return None

    date_str = date_str.strip()

    # Try dateutil first (very flexible)
    try:
        parsed = dateutil_parser.parse(date_str, dayfirst=True)
        return parsed.date()
    except Exception:
        pass

    return None


def parse_amount(amount_str: str) -> Optional[Decimal]:
    """Parse an amount string into a Decimal, handling Indian number formats."""
    if not amount_str:
        return None

    # Remove currency symbols, spaces, and common non-numeric chars
    cleaned = re.sub(r'[₹$€£¥\s,]', '', str(amount_str).strip())

    # Remove trailing Cr/Dr indicators
    cleaned = re.sub(r'(cr|dr)$', '', cleaned, flags=re.IGNORECASE).strip()

    if not cleaned:
        return None

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def clean_description(desc: str) -> str:
    """Clean and normalize a transaction description."""
    if not desc:
        return ''

    # Remove excess whitespace
    desc = ' '.join(desc.split())

    # Remove common noise patterns
    noise_patterns = [
        r'UPI-REF\d+',
        r'NEFT/\d+/',
        r'IMPS/\d+/',
        r'\b\d{10,}\b',  # Remove long numeric strings (transaction IDs embedded in desc)
    ]

    for pattern in noise_patterns:
        desc = re.sub(pattern, '', desc, flags=re.IGNORECASE)

    return ' '.join(desc.split()).strip()


def determine_transaction_type(debit: str, credit: str, amount: str, description: str) -> tuple:
    """
    Determine if a transaction is debit or credit, and resolve the final amount.
    Returns (type, amount_decimal)
    """
    debit_amount = parse_amount(debit) if debit else None
    credit_amount = parse_amount(credit) if credit else None
    generic_amount = parse_amount(amount) if amount else None

    # Check description for Cr/Dr suffix
    desc_lower = (description or '').lower()

    if debit_amount and debit_amount > 0:
        return 'debit', debit_amount
    elif credit_amount and credit_amount > 0:
        return 'credit', credit_amount
    elif generic_amount and generic_amount > 0:
        # Try to determine from description
        if desc_lower.endswith('cr') or 'credited' in desc_lower or 'salary' in desc_lower or 'interest' in desc_lower:
            return 'credit', generic_amount
        return 'debit', generic_amount

    return 'debit', Decimal('0.00')
