"""Buyer CRUD. Buyers with bids or sales are deactivated, never hard-deleted."""

from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from mysql.connector import errorcode

from app.auth import role_required
from app.database import MySQLError, execute, query_all, query_one
from app.helpers import EMAIL_RE, PHONE_RE, next_code, parse_date

buyers_bp = Blueprint("buyers", __name__, url_prefix="/buyers")
BUYER_ROLES = ("ADMIN", "OPERATOR")


def validate_buyer(form):
    errors = {}
    data = {
        "business_name": (form.get("business_name") or "").strip(),
        "contact_person": (form.get("contact_person") or "").strip(),
        "phone": (form.get("phone") or "").strip(),
        "email": (form.get("email") or "").strip() or None,
        "address": (form.get("address") or "").strip(),
        "registration_date": parse_date(form.get("registration_date"), "registration_date", errors),
    }
    if len(data["business_name"]) < 2:
        errors["business_name"] = "Enter a business name."
    if len(data["contact_person"]) < 2:
        errors["contact_person"] = "Enter a contact person."
    if not PHONE_RE.match(data["phone"]):
        errors["phone"] = "Enter a valid phone number (8–20 digits)."
    if data["email"] and not EMAIL_RE.match(data["email"]):
        errors["email"] = "Enter a valid email address, or leave it blank."
    if len(data["address"]) < 5:
        errors["address"] = "Enter an address."
    return data, errors


def buyer_history_count(buyer_id):
    bids = query_one("SELECT COUNT(*) AS n FROM bids WHERE buyer_id = %s", (buyer_id,))
    sales = query_one("SELECT COUNT(*) AS n FROM successful_sales WHERE buyer_id = %s", (buyer_id,))
    return int(bids["n"] if bids else 0) + int(sales["n"] if sales else 0)


@buyers_bp.route("/")
@role_required(*BUYER_ROLES)
def index():
    q = (request.args.get("q") or "").strip()
    status = request.args.get("status") or "all"
    like = f"%{q}%"
    extra = "AND is_active = 1" if status == "active" else "AND is_active = 0" if status == "inactive" else ""
    try:
        buyers = query_all(
            f"""
            SELECT buyer_id, buyer_code, business_name, contact_person, phone, email,
                   registration_date, is_active
            FROM buyers
            WHERE (%s = '' OR buyer_code LIKE %s OR business_name LIKE %s
                   OR contact_person LIKE %s OR phone LIKE %s)
            {extra}
            ORDER BY business_name
            """,
            (q, like, like, like, like),
        )
    except RuntimeError:
        flash("Cannot reach the database. Check MySQL and .env.", "danger")
        buyers = []
    return render_template("buyers/index.html", buyers=buyers, q=q, status=status)


@buyers_bp.route("/create", methods=["GET", "POST"])
@role_required(*BUYER_ROLES)
def create():
    form = {
        "business_name": "",
        "contact_person": "",
        "phone": "",
        "email": "",
        "address": "",
        "registration_date": date.today().isoformat(),
    }
    errors = {}
    if request.method == "POST":
        form, errors = validate_buyer(request.form)
        if form["registration_date"]:
            form["registration_date"] = form["registration_date"].isoformat()
        if not errors:
            code = next_code("buyers", "buyer_code", "BUY-")
            try:
                buyer_id, _ = execute(
                    """
                    INSERT INTO buyers (
                        buyer_code, business_name, contact_person, phone, email,
                        address, registration_date, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                    """,
                    (
                        code,
                        form["business_name"],
                        form["contact_person"],
                        form["phone"],
                        form["email"],
                        form["address"],
                        form["registration_date"],
                    ),
                )
            except MySQLError as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    flash("That buyer code is already in use. Try again.", "danger")
                else:
                    flash("Could not save the buyer.", "danger")
            else:
                flash(f"Buyer {code} was registered.", "success")
                return redirect(url_for("buyers.view", buyer_id=buyer_id))
    return render_template("buyers/create.html", form=form, errors=errors)


@buyers_bp.route("/<int:buyer_id>")
@role_required(*BUYER_ROLES)
def view(buyer_id):
    buyer = query_one("SELECT * FROM buyers WHERE buyer_id = %s", (buyer_id,))
    if buyer is None:
        flash("Buyer not found.", "warning")
        return redirect(url_for("buyers.index"))
    return render_template(
        "buyers/view.html",
        buyer=buyer,
        history_count=buyer_history_count(buyer_id),
    )


@buyers_bp.route("/<int:buyer_id>/edit", methods=["GET", "POST"])
@role_required(*BUYER_ROLES)
def edit(buyer_id):
    buyer = query_one("SELECT * FROM buyers WHERE buyer_id = %s", (buyer_id,))
    if buyer is None:
        flash("Buyer not found.", "warning")
        return redirect(url_for("buyers.index"))
    form = {
        "business_name": buyer["business_name"],
        "contact_person": buyer["contact_person"],
        "phone": buyer["phone"],
        "email": buyer["email"] or "",
        "address": buyer["address"],
        "registration_date": buyer["registration_date"].isoformat()
        if hasattr(buyer["registration_date"], "isoformat")
        else str(buyer["registration_date"]),
    }
    errors = {}
    if request.method == "POST":
        form, errors = validate_buyer(request.form)
        if form["registration_date"]:
            form["registration_date"] = form["registration_date"].isoformat()
        if not errors:
            execute(
                """
                UPDATE buyers
                SET business_name = %s, contact_person = %s, phone = %s, email = %s,
                    address = %s, registration_date = %s
                WHERE buyer_id = %s
                """,
                (
                    form["business_name"],
                    form["contact_person"],
                    form["phone"],
                    form["email"],
                    form["address"],
                    form["registration_date"],
                    buyer_id,
                ),
            )
            flash("Buyer details were updated.", "success")
            return redirect(url_for("buyers.view", buyer_id=buyer_id))
    return render_template("buyers/edit.html", buyer=buyer, form=form, errors=errors)


@buyers_bp.route("/<int:buyer_id>/deactivate", methods=["POST"])
@role_required(*BUYER_ROLES)
def deactivate(buyer_id):
    buyer = query_one("SELECT * FROM buyers WHERE buyer_id = %s", (buyer_id,))
    if buyer is None:
        flash("Buyer not found.", "warning")
        return redirect(url_for("buyers.index"))
    execute("UPDATE buyers SET is_active = 0 WHERE buyer_id = %s", (buyer_id,))
    history = buyer_history_count(buyer_id)
    if history:
        flash(
            f"{buyer['buyer_code']} was deactivated. "
            "Bid and sale history was kept — the buyer was not deleted.",
            "success",
        )
    else:
        flash(f"{buyer['buyer_code']} was deactivated.", "success")
    return redirect(url_for("buyers.view", buyer_id=buyer_id))


@buyers_bp.route("/<int:buyer_id>/reactivate", methods=["POST"])
@role_required(*BUYER_ROLES)
def reactivate(buyer_id):
    execute("UPDATE buyers SET is_active = 1 WHERE buyer_id = %s", (buyer_id,))
    flash("Buyer is active again.", "success")
    return redirect(url_for("buyers.view", buyer_id=buyer_id))
