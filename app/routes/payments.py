"""Record payments through sp_record_payment (overpay guard + sale status)."""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.auth import role_required
from app.database import MySQLError, callproc, query_all, query_one
from app.helpers import flash_db_error, next_timed_reference, parse_datetime, parse_decimal

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")
FINANCE_ROLES = ("ADMIN", "FINANCE")
METHODS = ("BANK_TRANSFER", "CASH", "MOBILE_MONEY")
STATUSES = ("PENDING", "VERIFIED", "REJECTED")


@payments_bp.route("/")
@role_required(*FINANCE_ROLES)
def index():
    q = (request.args.get("q") or "").strip()
    like = f"%{q}%"
    try:
        payments = query_all(
            """
            SELECT p.payment_id, p.payment_reference, p.amount, p.payment_method,
                   p.payment_date, p.status, s.sale_reference, byr.business_name
            FROM payments AS p
            INNER JOIN successful_sales AS s ON s.sale_id = p.sale_id
            INNER JOIN buyers AS byr ON byr.buyer_id = s.buyer_id
            WHERE (%s = '' OR p.payment_reference LIKE %s OR s.sale_reference LIKE %s
                   OR byr.business_name LIKE %s)
            ORDER BY p.payment_date DESC
            """,
            (q, like, like, like),
        )
    except RuntimeError:
        flash("Cannot reach the database. Check MySQL and .env.", "danger")
        payments = []
    return render_template("payments/index.html", payments=payments, q=q)


@payments_bp.route("/create", methods=["GET", "POST"])
@role_required(*FINANCE_ROLES)
def create():
    selected = request.args.get("sale_id") or request.form.get("sale_id") or ""
    form = {
        "sale_id": str(selected),
        "amount": request.form.get("amount", ""),
        "payment_method": request.form.get("payment_method", "BANK_TRANSFER"),
        "payment_date": request.form.get("payment_date", ""),
        "status": request.form.get("status", "VERIFIED"),
    }
    errors = {}
    sales = query_all(
        """
        SELECT s.sale_id, s.sale_reference, s.sale_amount, s.status,
               v.outstanding_balance, byr.business_name
        FROM successful_sales AS s
        INNER JOIN vw_sales_payment_summary AS v ON v.sale_id = s.sale_id
        INNER JOIN buyers AS byr ON byr.buyer_id = s.buyer_id
        WHERE s.status IN ('PAYMENT_PENDING', 'PARTIALLY_PAID')
        ORDER BY s.sale_date
        """,
        (),
    )
    if request.method == "POST":
        amount = parse_decimal(form["amount"], "amount", errors, minimum=0)
        paid_at = parse_datetime(form["payment_date"], "payment_date", errors)
        if not str(form["sale_id"]).isdigit():
            errors["sale_id"] = "Choose a sale."
        if form["payment_method"] not in METHODS:
            errors["payment_method"] = "Choose a payment method."
        if form["status"] not in STATUSES:
            errors["status"] = "Choose a payment status."
        if not errors:
            reference = next_timed_reference("PAY-")
            try:
                rows = callproc(
                    "sp_record_payment",
                    (
                        int(form["sale_id"]),
                        amount,
                        reference,
                        form["payment_method"],
                        paid_at,
                        session["user_id"],
                        form["status"],
                    ),
                )
            except MySQLError as err:
                flash_db_error(err, "Could not record the payment.")
            except RuntimeError:
                flash("Cannot reach the database. Check MySQL and .env.", "danger")
            else:
                result = rows[0] if rows else {}
                flash(result.get("message") or f"Payment {reference} recorded.", "success")
                return redirect(url_for("sales.view", sale_id=int(form["sale_id"])))
    return render_template(
        "payments/create.html",
        form=form,
        errors=errors,
        sales=sales,
        methods=METHODS,
        statuses=STATUSES,
    )
