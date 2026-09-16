"""SQL-powered management reports. Figures always come from MySQL, never literals."""

from flask import Blueprint, flash, render_template

from app.auth import role_required
from app.database import query_all

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")
REPORT_ROLES = ("ADMIN", "FINANCE", "VIEWER")


def _safe(sql, params=()):
    try:
        return query_all(sql, params)
    except RuntimeError:
        flash("Cannot reach the database. Check MySQL and .env.", "danger")
        return []


@reports_bp.route("/")
@role_required(*REPORT_ROLES)
def index():
    farmer_supply = _safe(
        """
        SELECT CONCAT(f.first_name, ' ', f.last_name) AS farmer,
               f.farm_name,
               pt.name AS produce_type,
               COUNT(pl.lot_id) AS number_of_lots,
               SUM(pl.quantity) AS total_quantity,
               AVG(pl.quantity) AS average_lot_quantity,
               MIN(pl.quantity) AS smallest_lot,
               MAX(pl.quantity) AS largest_lot,
               pl.unit_of_measure
        FROM farmers AS f
        INNER JOIN produce_lots AS pl ON pl.farmer_id = f.farmer_id
        INNER JOIN produce_types AS pt ON pt.produce_type_id = pl.produce_type_id
        GROUP BY f.farmer_id, f.first_name, f.last_name, f.farm_name,
                 pt.produce_type_id, pt.name, pl.unit_of_measure
        ORDER BY f.last_name, pt.name
        """
    )
    buyer_purchasing = _safe(
        """
        SELECT byr.buyer_code,
               byr.business_name,
               COUNT(s.sale_id) AS number_of_purchases,
               SUM(s.sale_amount) AS total_purchase_value,
               AVG(s.sale_amount) AS average_purchase_value
        FROM buyers AS byr
        INNER JOIN successful_sales AS s ON s.buyer_id = byr.buyer_id
        GROUP BY byr.buyer_id, byr.buyer_code, byr.business_name
        ORDER BY total_purchase_value DESC
        """
    )
    sales_summary = _safe(
        """
        SELECT s.sale_reference,
               byr.business_name AS buyer,
               pt.name AS produce,
               pl.quantity,
               pl.unit_of_measure,
               s.sale_amount,
               s.status AS payment_status
        FROM successful_sales AS s
        INNER JOIN buyers AS byr ON byr.buyer_id = s.buyer_id
        INNER JOIN produce_lots AS pl ON pl.lot_id = s.lot_id
        INNER JOIN produce_types AS pt ON pt.produce_type_id = pl.produce_type_id
        ORDER BY s.sale_date DESC
        """
    )
    outstanding = _safe(
        """
        SELECT v.sale_reference,
               v.buyer,
               v.sale_amount,
               v.total_verified_payments AS amount_paid,
               v.outstanding_balance
        FROM vw_sales_payment_summary AS v
        WHERE v.outstanding_balance > 0
          AND v.sale_status <> 'CANCELLED'
        ORDER BY v.outstanding_balance DESC
        """
    )
    return render_template(
        "reports/index.html",
        farmer_supply=farmer_supply,
        buyer_purchasing=buyer_purchasing,
        sales_summary=sales_summary,
        outstanding=outstanding,
    )
