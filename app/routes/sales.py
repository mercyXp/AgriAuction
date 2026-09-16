"""Successful sales created only by closing an auction — never by a blank form."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.auth import role_required
from app.database import query_all, query_one

sales_bp = Blueprint("sales", __name__, url_prefix="/sales")
SALE_ROLES = ("ADMIN", "AUCTION_CLERK", "FINANCE")


@sales_bp.route("/")
@role_required(*SALE_ROLES)
def index():
    q = (request.args.get("q") or "").strip()
    status = request.args.get("status") or "all"
    like = f"%{q}%"
    extra = "AND s.status = %s" if status != "all" else ""
    params = [q, like, like, like]
    if status != "all":
        params.append(status)
    try:
        sales = query_all(
            f"""
            SELECT s.sale_id, s.sale_reference, s.sale_amount, s.sale_date, s.status,
                   pl.lot_id, pl.lot_number, pt.name AS produce_name,
                   byr.buyer_code, byr.business_name,
                   v.total_verified_payments, v.outstanding_balance
            FROM successful_sales AS s
            INNER JOIN produce_lots AS pl ON pl.lot_id = s.lot_id
            INNER JOIN produce_types AS pt ON pt.produce_type_id = pl.produce_type_id
            INNER JOIN buyers AS byr ON byr.buyer_id = s.buyer_id
            INNER JOIN vw_sales_payment_summary AS v ON v.sale_id = s.sale_id
            WHERE (%s = '' OR s.sale_reference LIKE %s OR pl.lot_number LIKE %s
                   OR byr.business_name LIKE %s)
            {extra}
            ORDER BY s.sale_date DESC
            """,
            tuple(params),
        )
    except RuntimeError:
        flash("Cannot reach the database. Check MySQL and .env.", "danger")
        sales = []
    return render_template("sales/index.html", sales=sales, q=q, status=status)


@sales_bp.route("/<int:sale_id>")
@role_required(*SALE_ROLES)
def view(sale_id):
    sale = query_one(
        """
        SELECT s.*, pl.lot_id, pl.lot_number, pl.quantity, pl.unit_of_measure,
               pl.status AS lot_status, pt.name AS produce_name,
               byr.buyer_code, byr.business_name, byr.contact_person, byr.phone,
               b.bid_id, b.bid_amount, b.bid_time,
               v.total_verified_payments, v.outstanding_balance
        FROM successful_sales AS s
        INNER JOIN produce_lots AS pl ON pl.lot_id = s.lot_id
        INNER JOIN produce_types AS pt ON pt.produce_type_id = pl.produce_type_id
        INNER JOIN buyers AS byr ON byr.buyer_id = s.buyer_id
        INNER JOIN bids AS b ON b.bid_id = s.winning_bid_id
        INNER JOIN vw_sales_payment_summary AS v ON v.sale_id = s.sale_id
        WHERE s.sale_id = %s
        """,
        (sale_id,),
    )
    if sale is None:
        flash("Sale not found.", "warning")
        return redirect(url_for("sales.index"))
    payments = query_all(
        """
        SELECT p.*, CONCAT(st.first_name, ' ', st.last_name) AS recorded_by_name
        FROM payments AS p
        INNER JOIN staff AS st ON st.staff_id = p.recorded_by
        WHERE p.sale_id = %s
        ORDER BY p.payment_date
        """,
        (sale_id,),
    )
    collection = query_one(
        "SELECT * FROM collections WHERE sale_id = %s",
        (sale_id,),
    )
    return render_template(
        "sales/view.html",
        sale=sale,
        payments=payments,
        collection=collection,
    )
