"""Farmer CRUD. Farmers with lots are deactivated, never hard-deleted."""

import re
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from mysql.connector import errorcode

from app.auth import role_required
from app.database import MySQLError, execute, query_all, query_one

farmers_bp = Blueprint("farmers", __name__, url_prefix="/farmers")

FARMER_ROLES = ("ADMIN", "OPERATOR")
PHONE_RE = re.compile(r"^[0-9+\-\s]{8,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def next_farmer_code():
    row = query_one(
        "SELECT MAX(CAST(SUBSTRING(farmer_code, 5) AS UNSIGNED)) AS n FROM farmers"
    )
    number = int(row["n"] or 0) + 1 if row else 1
    return f"FRM-{number:04d}"


def farmer_lot_count(farmer_id):
    row = query_one(
        "SELECT COUNT(*) AS n FROM produce_lots WHERE farmer_id = %s",
        (farmer_id,),
    )
    return int(row["n"]) if row else 0


def validate_farmer(form):
    errors = {}
    data = {
        "first_name": (form.get("first_name") or "").strip(),
        "last_name": (form.get("last_name") or "").strip(),
        "phone": (form.get("phone") or "").strip(),
        "email": (form.get("email") or "").strip() or None,
        "address": (form.get("address") or "").strip(),
        "farm_name": (form.get("farm_name") or "").strip(),
        "registration_date": (form.get("registration_date") or "").strip(),
    }

    if len(data["first_name"]) < 2:
        errors["first_name"] = "Enter a first name."
    if len(data["last_name"]) < 2:
        errors["last_name"] = "Enter a last name."
    if not PHONE_RE.match(data["phone"]):
        errors["phone"] = "Enter a valid phone number (8–20 digits)."
    if data["email"] and not EMAIL_RE.match(data["email"]):
        errors["email"] = "Enter a valid email address, or leave it blank."
    if len(data["address"]) < 5:
        errors["address"] = "Enter a farm or postal address."
    if len(data["farm_name"]) < 2:
        errors["farm_name"] = "Enter a farm name."
    if not data["registration_date"]:
        errors["registration_date"] = "Enter the registration date."
    else:
        try:
            date.fromisoformat(data["registration_date"])
        except ValueError:
            errors["registration_date"] = "Use a valid date (YYYY-MM-DD)."

    return data, errors


@farmers_bp.route("/")
@role_required(*FARMER_ROLES)
def index():
    q = (request.args.get("q") or "").strip()
    status = request.args.get("status") or "all"
    like = f"%{q}%"
    if status == "active":
        status_sql = "AND is_active = 1"
    elif status == "inactive":
        status_sql = "AND is_active = 0"
    else:
        status_sql = ""
        status = "all"

    # Search terms are still parameterized; only the status clause is chosen here.
    try:
        farmers = query_all(
            f"""
            SELECT farmer_id, farmer_code, first_name, last_name, phone, email,
                   farm_name, registration_date, is_active
            FROM farmers
            WHERE (
                %s = ''
                OR farmer_code LIKE %s
                OR first_name LIKE %s
                OR last_name LIKE %s
                OR farm_name LIKE %s
                OR phone LIKE %s
            )
            {status_sql}
            ORDER BY last_name, first_name
            """,
            (q, like, like, like, like, like),
        )
    except RuntimeError:
        flash("Cannot reach the database. Check MySQL and .env.", "danger")
        farmers = []
    return render_template(
        "farmers/index.html",
        farmers=farmers,
        q=q,
        status=status,
    )


@farmers_bp.route("/create", methods=["GET", "POST"])
@role_required(*FARMER_ROLES)
def create():
    form = {
        "first_name": "",
        "last_name": "",
        "phone": "",
        "email": "",
        "address": "",
        "farm_name": "",
        "registration_date": date.today().isoformat(),
    }
    errors = {}
    if request.method == "POST":
        form, errors = validate_farmer(request.form)
        if not errors:
            code = next_farmer_code()
            try:
                farmer_id, _ = execute(
                    """
                    INSERT INTO farmers (
                        farmer_code, first_name, last_name, phone, email,
                        address, farm_name, registration_date, is_active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
                    """,
                    (
                        code,
                        form["first_name"],
                        form["last_name"],
                        form["phone"],
                        form["email"],
                        form["address"],
                        form["farm_name"],
                        form["registration_date"],
                    ),
                )
            except MySQLError as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    errors["farmer_code"] = "That farmer code is already in use. Try again."
                else:
                    flash("Could not save the farmer. Check the database connection.", "danger")
                    return render_template("farmers/create.html", form=form, errors=errors)
            else:
                flash(f"Farmer {code} was registered.", "success")
                return redirect(url_for("farmers.view", farmer_id=farmer_id))
    return render_template("farmers/create.html", form=form, errors=errors)


@farmers_bp.route("/<int:farmer_id>")
@role_required(*FARMER_ROLES)
def view(farmer_id):
    farmer = query_one("SELECT * FROM farmers WHERE farmer_id = %s", (farmer_id,))
    if farmer is None:
        flash("Farmer not found.", "warning")
        return redirect(url_for("farmers.index"))
    return render_template(
        "farmers/view.html",
        farmer=farmer,
        lot_count=farmer_lot_count(farmer_id),
    )


@farmers_bp.route("/<int:farmer_id>/edit", methods=["GET", "POST"])
@role_required(*FARMER_ROLES)
def edit(farmer_id):
    farmer = query_one("SELECT * FROM farmers WHERE farmer_id = %s", (farmer_id,))
    if farmer is None:
        flash("Farmer not found.", "warning")
        return redirect(url_for("farmers.index"))

    form = {
        "first_name": farmer["first_name"],
        "last_name": farmer["last_name"],
        "phone": farmer["phone"],
        "email": farmer["email"] or "",
        "address": farmer["address"],
        "farm_name": farmer["farm_name"],
        "registration_date": farmer["registration_date"].isoformat()
        if hasattr(farmer["registration_date"], "isoformat")
        else str(farmer["registration_date"]),
    }
    errors = {}
    if request.method == "POST":
        form, errors = validate_farmer(request.form)
        if not errors:
            execute(
                """
                UPDATE farmers
                SET first_name = %s,
                    last_name = %s,
                    phone = %s,
                    email = %s,
                    address = %s,
                    farm_name = %s,
                    registration_date = %s
                WHERE farmer_id = %s
                """,
                (
                    form["first_name"],
                    form["last_name"],
                    form["phone"],
                    form["email"],
                    form["address"],
                    form["farm_name"],
                    form["registration_date"],
                    farmer_id,
                ),
            )
            flash("Farmer details were updated.", "success")
            return redirect(url_for("farmers.view", farmer_id=farmer_id))
    return render_template(
        "farmers/edit.html",
        farmer=farmer,
        form=form,
        errors=errors,
    )


@farmers_bp.route("/<int:farmer_id>/deactivate", methods=["POST"])
@role_required(*FARMER_ROLES)
def deactivate(farmer_id):
    farmer = query_one("SELECT * FROM farmers WHERE farmer_id = %s", (farmer_id,))
    if farmer is None:
        flash("Farmer not found.", "warning")
        return redirect(url_for("farmers.index"))
    execute(
        "UPDATE farmers SET is_active = 0 WHERE farmer_id = %s",
        (farmer_id,),
    )
    lots = farmer_lot_count(farmer_id)
    if lots:
        flash(
            f"{farmer['farmer_code']} was deactivated. "
            f"{lots} historical lot(s) were kept — the farmer was not deleted.",
            "success",
        )
    else:
        flash(f"{farmer['farmer_code']} was deactivated.", "success")
    return redirect(url_for("farmers.view", farmer_id=farmer_id))


@farmers_bp.route("/<int:farmer_id>/reactivate", methods=["POST"])
@role_required(*FARMER_ROLES)
def reactivate(farmer_id):
    farmer = query_one("SELECT * FROM farmers WHERE farmer_id = %s", (farmer_id,))
    if farmer is None:
        flash("Farmer not found.", "warning")
        return redirect(url_for("farmers.index"))
    execute(
        "UPDATE farmers SET is_active = 1 WHERE farmer_id = %s",
        (farmer_id,),
    )
    flash(f"{farmer['farmer_code']} is active again.", "success")
    return redirect(url_for("farmers.view", farmer_id=farmer_id))
