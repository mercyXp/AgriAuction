"""Shared validation helpers. Table names in next_code() are never user input."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.database import query_one

PHONE_RE = re.compile(r"^[0-9+\-\s]{8,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def next_code(table, column, prefix):
    """Next FRM-0001 / BUY-0001 style code. table and column are fixed in code."""
    allowed = {
        ("farmers", "farmer_code"),
        ("buyers", "buyer_code"),
        ("depots", "depot_code"),
        ("produce_lots", "lot_number"),
        ("payments", "payment_reference"),
        ("collections", "collection_reference"),
    }
    if (table, column) not in allowed:
        raise ValueError("Unsupported code table")
    start = len(prefix) + 1
    row = query_one(
        f"SELECT MAX(CAST(SUBSTRING({column}, %s) AS UNSIGNED)) AS n FROM {table}",
        (start,),
    )
    number = int(row["n"] or 0) + 1 if row else 1
    return f"{prefix}{number:04d}"


def next_lot_number(year=2026):
    prefix = f"LOT-{year}-"
    start = len(prefix) + 1
    row = query_one(
        "SELECT MAX(CAST(SUBSTRING(lot_number, %s) AS UNSIGNED)) AS n "
        "FROM produce_lots WHERE lot_number LIKE %s",
        (start, prefix + "%"),
    )
    number = int(row["n"] or 0) + 1 if row else 1
    return f"{prefix}{number:04d}"


def next_timed_reference(prefix):
    """PAY- / COL- reference unique enough for one staff member."""
    from datetime import datetime

    return f"{prefix}{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def flash_db_error(err, fallback):
    """Show SIGNAL business messages; hide other MySQL errors from users."""
    from flask import current_app, flash

    errno = getattr(err, "errno", None)
    sqlstate = getattr(err, "sqlstate", None)
    message = getattr(err, "msg", "") or fallback
    if errno == 1644 or sqlstate == "45000":
        flash(message, "danger")
        return
    current_app.logger.error("MySQL error errno=%s", errno)
    flash(fallback, "danger")


def parse_date(value, field, errors):
    text = (value or "").strip()
    if not text:
        errors[field] = "This date is required."
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        errors[field] = "Use a valid date."
        return None


def parse_datetime(value, field, errors):
    text = (value or "").strip()
    if not text:
        errors[field] = "This date and time is required."
        return None
    text = text.replace("T", " ")
    if len(text) == 16:
        text += ":00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        errors[field] = "Use a valid date and time."
        return None


def parse_decimal(value, field, errors, minimum=None):
    text = (value or "").strip()
    if not text:
        errors[field] = "Enter a number."
        return None
    try:
        amount = Decimal(text)
    except InvalidOperation:
        errors[field] = "Enter a valid number."
        return None
    if minimum is not None and amount <= minimum:
        errors[field] = f"Enter a value greater than {minimum}."
        return None
    return amount


def dt_local(value):
    """Format a datetime for an HTML datetime-local input."""
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%dT%H:%M")
    return str(value)[:16].replace(" ", "T")
