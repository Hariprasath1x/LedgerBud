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


def extract_structured_tokens(raw_desc: str) -> dict:
    """Extract structural tokens (UPI IDs, VPAs, Merchant IDs) from raw description."""
    tokens = {
        "upi_id": None,
        "vpa": None,
        "merchant_id": None,
        "psp_ref": None,
    }
    if not raw_desc:
        return tokens

    desc = raw_desc.upper()

    # Match common UPI / VPA formats (e.g. name@bank or UPI/NAME@BANK/...)
    vpa_match = re.search(r'([A-Z0-9.\-_]+@[A-Z]+)', desc)
    if vpa_match:
        tokens["vpa"] = vpa_match.group(1).lower()
        tokens["upi_id"] = tokens["vpa"]  # VPA is often synonymous with UPI ID

    # Match merchant identifiers if labelled explicitly
    mid_match = re.search(r'MID[/\-\s]+([A-Z0-9]+)', desc)
    if mid_match:
        tokens["merchant_id"] = mid_match.group(1)
        
    return tokens


def clean_description(desc: str) -> str:
    """Clean and normalize a transaction description."""
    if not desc:
        return ''

    # Remove excess whitespace
    desc = ' '.join(desc.split())

    # We do NOT want to aggressively remove noise here anymore because we have a dedicated engine,
    # but we still clean up formatting for easier reading.
    # Keep it simple, just uppercase and strip excess spaces.
    desc = ' '.join(desc.split()).strip()
    return desc


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
