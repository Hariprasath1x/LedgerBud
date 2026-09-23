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


