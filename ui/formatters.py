"""Formatting utilities for financial data, dates, and percentages."""

from datetime import datetime, date


def format_currency(amount: float | int | None) -> str:
    """Format numeric value to Indian Currency format (₹1,25,000.00)."""
    if amount is None:
        return "₹0.00"

    try:
        val = float(amount)
    except (ValueError, TypeError):
        return "₹0.00"

    is_negative = val < 0
    val = abs(val)

    # Split into rupees and paise
    s = f"{val:.2f}"
    rupees, paise = s.split(".")

    last_three = rupees[-3:]
    other_rupees = rupees[:-3]

    if other_rupees:
        chunks = []
        i = len(other_rupees)
        while i > 0:
            if i - 2 >= 0:
                chunks.insert(0, other_rupees[i-2:i])
            else:
                chunks.insert(0, other_rupees[0:i])
            i -= 2
        formatted_rupees = ",".join(chunks) + "," + last_three
    else:
        formatted_rupees = last_three

    sign = "-" if is_negative else ""
    return f"{sign}₹{formatted_rupees}.{paise}"


def format_percentage(val: float | int | None) -> str:
    """Format numeric value to percentage string."""
    if val is None:
        return "0.0%"
    try:
        return f"{float(val):.1f}%"
    except (ValueError, TypeError):
        return "0.0%"


def format_date(date_val: str | date | datetime | None) -> str:
    """Format dates to human-friendly financial display (e.g., 15 Oct 2026)."""
    if date_val is None:
        return "-"

    if isinstance(date_val, str):
        try:
            # Try parsing ISO date format first
            parsed_date = datetime.fromisoformat(date_val).date()
        except ValueError:
            try:
                # Try parsing format YYYY-MM-DD
                parsed_date = datetime.strptime(date_val, "%Y-%m-%d").date()
            except ValueError:
                return date_val
    elif isinstance(date_val, datetime):
        parsed_date = date_val.date()
    else:
        parsed_date = date_val

    return parsed_date.strftime("%d %b %Y")


def format_month(month_str: str) -> str:
    """Format month string like '2026-07' to 'Jul 2026'."""
    try:
        dt = datetime.strptime(month_str, "%Y-%m")
        return dt.strftime("%b %Y")
    except Exception:
        return month_str
