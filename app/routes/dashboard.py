"""Staff dashboard with live MySQL statistics and Chart.js summaries."""

import json
from decimal import Decimal
from datetime import date, datetime

from flask import Blueprint, render_template, session

from app.auth import login_required, role_label, role_required
from app.database import MySQLError, query_all, query_one

dashboard_bp = Blueprint("dashboard", __name__)


def _json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _count(sql, params=()):
    try:
        row = query_one(sql, params)
        return int(row["n"]) if row and row["n"] is not None else 0
    except (RuntimeError, MySQLError):
        return None


def _amount(sql, params=()):
    try:
        row = query_one(sql, params)
        if row is None or row["n"] is None:
            return 0
        return row["n"]
    except (RuntimeError, MySQLError):
        return None


def _rows(sql, params=()):
    try:
        return query_all(sql, params)
    except (RuntimeError, MySQLError):
        return None


@dashboard_bp.route("/dashboard")
@login_required
def index():
    stats = {
        "farmers": _count("SELECT COUNT(*) AS n FROM farmers WHERE is_active = 1"),
        "buyers": _count("SELECT COUNT(*) AS n FROM buyers WHERE is_active = 1"),
        "open_lots": _count("SELECT COUNT(*) AS n FROM produce_lots WHERE status = 'OPEN'"),
        "lots_sold": _count(
            "SELECT COUNT(*) AS n FROM produce_lots WHERE status IN ('SOLD', 'COLLECTED')"
        ),
        "total_sales": _amount("SELECT COALESCE(SUM(sale_amount), 0) AS n FROM successful_sales"),
        "verified_payments": _amount(
            "SELECT COALESCE(SUM(amount), 0) AS n FROM payments WHERE status = 'VERIFIED'"
        ),
        "outstanding": _amount(
            """
            SELECT COALESCE(SUM(outstanding_balance), 0) AS n
            FROM vw_sales_payment_summary
            WHERE sale_status IN ('PAYMENT_PENDING', 'PARTIALLY_PAID')
            """
        ),
        "pending_collections": _count(
            """
            SELECT COUNT(*) AS n
            FROM successful_sales AS s
            LEFT JOIN collections AS c ON c.sale_id = s.sale_id
            WHERE s.status = 'PAID' AND c.collection_id IS NULL
            """
        ),
    }
    charts = {
        "sales_by_type": _rows(
            """
            SELECT pt.name AS label, COALESCE(SUM(s.sale_amount), 0) AS total
            FROM produce_types AS pt
            LEFT JOIN produce_lots AS pl ON pl.produce_type_id = pt.produce_type_id
            LEFT JOIN successful_sales AS s ON s.lot_id = pl.lot_id
            GROUP BY pt.produce_type_id, pt.name
            ORDER BY total DESC
            """
        ),
        "monthly_sales": _rows(
            """
            SELECT DATE_FORMAT(sale_date, '%Y-%m') AS label,
                   SUM(sale_amount) AS total
            FROM successful_sales
            GROUP BY DATE_FORMAT(sale_date, '%Y-%m')
            ORDER BY label
            """
        ),
        "lot_status": _rows(
            """
            SELECT status AS label, COUNT(*) AS total
            FROM produce_lots
            GROUP BY status
            ORDER BY status
            """
        ),
        "payment_status": _rows(
            """
            SELECT status AS label, COUNT(*) AS total
            FROM payments
            GROUP BY status
            ORDER BY status
            """
        ),
    }
    db_ok = all(value is not None for value in stats.values()) and all(
        value is not None for value in charts.values()
    )
    chart_json = json.dumps(charts if db_ok else {}, default=_json_default)
    return render_template(
        "app/dashboard.html",
        role_label=role_label(session.get("role")),
        stats=stats,
        db_ok=db_ok,
        chart_json=chart_json,
    )


@dashboard_bp.route("/administration")
@role_required("ADMIN")
def administration():
    """ADMIN-only database administration notes."""
    return render_template("app/administration.html")
