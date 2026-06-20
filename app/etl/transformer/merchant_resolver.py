"""
Merchant Resolver
Identifies merchants from transaction descriptions using:
1. Exact keyword match against merchant dictionary
2. Fuzzy matching for near-matches
3. UPI/NEFT/IMPS pattern extraction
"""
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# UPI merchant patterns
UPI_PATTERNS = [
    r'UPI[\/\-\s]+(?:TO\s+)?([A-Za-z0-9\s]+?)(?:[\/@\.\|]|$)',
    r'PAY(?:MENT)?\s+TO\s+([A-Za-z0-9\s]+?)(?:\s*-|\s*\||\s*$)',
]

# Patterns to strip from descriptions before merchant resolution
STRIP_PATTERNS = [
    r'UPI[-/]REF\w*\s*\d*',
    r'NEFT[-/]\w+[-/]',
    r'IMPS[-/]\w+[-/]',
    r'\b\d{12,}\b',
    r'@\w+',
    r'VPA\s+\w+',
    r'^\d+\s*',
]


def resolve_merchant(description: str, merchant_lookup: dict) -> Tuple[Optional[int], str]:
    """
    Resolve a raw transaction description to a merchant.
    Returns (merchant_id or None, canonical_merchant_name)
    """
    if not description:
        return None, ''

    # Step 1: Try UPI extraction
    upi_name = _extract_upi_merchant(description)

    # Step 2: Clean description for matching
    clean_desc = _clean_for_matching(description)

    # Try UPI name first, then clean description
    for candidate in ([upi_name] if upi_name else []) + [clean_desc, description]:
        if not candidate:
            continue

        result = _lookup_merchant(candidate, merchant_lookup)
        if result:
            return result

    # Return best guess merchant name
    best_name = upi_name or _extract_readable_name(clean_desc)
    return None, best_name


def _extract_upi_merchant(description: str) -> Optional[str]:
    """Extract merchant name from UPI transaction description."""
    for pattern in UPI_PATTERNS:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2:
                return name
    return None


def _clean_for_matching(description: str) -> str:
    """Strip noise from description for cleaner merchant matching."""
    cleaned = description.upper()
    for pattern in STRIP_PATTERNS:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
    return ' '.join(cleaned.split())


def _lookup_merchant(candidate: str, merchant_lookup: dict) -> Optional[Tuple[int, str]]:
    """
    merchant_lookup: dict of {keyword_lower: (merchant_id, canonical_name)}
    """
    candidate_lower = candidate.lower()

    # Exact keyword match
    for keyword, (merchant_id, canonical_name) in merchant_lookup.items():
        if keyword in candidate_lower:
            return merchant_id, canonical_name

    return None


def _extract_readable_name(description: str) -> str:
    """Extract a human-readable merchant name from cleaned description."""
    if not description:
        return 'Unknown'

    # Take first meaningful words
    words = description.split()
    readable = []
    for word in words[:4]:
        if len(word) > 2 and not word.isdigit():
            readable.append(word.title())

    return ' '.join(readable) if readable else description[:30].title()
