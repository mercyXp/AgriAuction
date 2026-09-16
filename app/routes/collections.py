"""Record collection of paid produce. Updates sale and lot in one transaction."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.auth import role_required
from app.database import MySQLError, execute, get_db, query_all, query_one
from app.helpers import flash_db_error, next_timed_reference, parse_datetime, parse_decimal

collections_bp = Blueprint("collections", __name__, url_prefix="/collections")
FINANCE_ROLES = ("ADMIN", "FINANCE")


@collections_bp.route("/")
@role_required(*FINANCE_ROLES)
def index():
    try:
        rows = query_all(
            """
            SELECT c.collection_id, c.collection_reference, c.collected_quantity,
                   c.collection_date, c.collected_by, s.sale_reference,
                   pl.lot_number, byr.business_name
            FROM collections AS c
            INNER JOIN successful_sales AS s ON s.sale_id = c.sale_id
            INNER JOIN produce_lots AS pl ON pl.lot_id = s.lot_id
            INNER JOIN buyers AS byr ON byr.buyer_id = s.buyer_id
            ORDER BY c.collection_date DESC
            """,
            (),
        )
        pending = query_all(
            """
            SELECT s.sale_id, s.sale_reference, pl.lot_number, byr.business_name
            FROM successful_sales AS s
            INNER JOIN produce_lots AS pl ON pl.lot_id = s.lot_id
            INNER JOIN buyers AS byr ON byr.buyer_id = s.buyer_id
            LEFT JOIN collections AS c ON c.sale_id = s.sale_id
            WHERE s.status = 'PAID' AND c.collection_id IS NULL
            ORDER BY s.sale_date
            """,
            (),
        )
    except RuntimeError:
        flash("Cannot reach the database. Check MySQL and .env.", "danger")
        rows = []
        pending = []
    return render_template("collections/index.html", rows=rows, pending=pending)


@collections_bp.route("/create", methods=["GET", "POST"])
@role_required(*FINANCE_ROLES)
def create():
    selected = request.args.get("sale_id") or request.form.get("sale_id") or ""
    form = {
        "sale_id": str(selected),
        "collected_quantity": request.form.get("collected_quantity", ""),
        "collection_date": request.form.get("collection_date", ""),
        "collected_by": request.form.get("collected_by", ""),
        "notes": request.form.get("notes", ""),
    }
    errors = {}
    sales = query_all(
        """
        SELECT s.sale_id, s.sale_reference, pl.lot_number, pl.quantity,
               pl.unit_of_measure, byr.business_name
        FROM successful_sales AS s
        INNER JOIN produce_lots AS pl ON pl.lot_id = s.lot_id
        INNER JOIN buyers AS byr ON byr.buyer_id = s.buyer_id
        LEFT JOIN collections AS c ON c.sale_id = s.sale_id
        WHERE s.status = 'PAID' AND c.collection_id IS NULL
        ORDER BY s.sale_date
        """,
        (),
    )
    if request.method == "POST":
        qty = parse_decimal(form["collected_quantity"], "collected_quantity", errors, minimum=0)
        collected_at = parse_datetime(form["collection_date"], "collection_date", errors)
        collected_by = (form["collected_by"] or "").strip()
        notes = (form["notes"] or "").strip() or None
        if not collected_by:
            errors["collected_by"] = "Enter who collected the produce."
        if not str(form["sale_id"]).isdigit():
            errors["sale_id"] = "Choose a paid sale."
        if not errors:
            db = get_db()
            try:
                sale = query_one(
                    """
                    SELECT s.sale_id, s.status, s.lot_id, pl.quantity
                    FROM successful_sales AS s
                    INNER JOIN produce_lots AS pl ON pl.lot_id = s.lot_id
                    WHERE s.sale_id = %s
                    FOR UPDATE
                    """,
                    (int(form["sale_id"]),),
                )
                if sale is None:
                    errors["sale_id"] = "Sale not found."
                    db.rollback()
                elif sale["status"] != "PAID":
                    errors["sale_id"] = "Produce can only be collected after the sale is fully paid."
                    db.rollback()
                elif qty > sale["quantity"]:
                    errors["collected_quantity"] = "Collected quantity cannot exceed the lot quantity."
                    db.rollback()
                else:
                    existing = query_one(
                        "SELECT collection_id FROM collections WHERE sale_id = %s",
                        (sale["sale_id"],),
                    )
                    if existing:
                        errors["sale_id"] = "This sale already has a collection record."
                        db.rollback()
                    else:
                        reference = next_timed_reference("COL-")
                        execute(
                            """
                            INSERT INTO collections (
                                sale_id, collection_reference, collected_quantity,
                                collection_date, collected_by, notes
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                sale["sale_id"],
                                reference,
                                qty,
                                collected_at,
                                collected_by,
                                notes,
                            ),
                            commit=False,
                        )
                        execute(
                            "UPDATE successful_sales SET status = 'COLLECTED' WHERE sale_id = %s",
                            (sale["sale_id"],),
                            commit=False,
                        )
                        execute(
                            "UPDATE produce_lots SET status = 'COLLECTED' WHERE lot_id = %s",
                            (sale["lot_id"],),
                            commit=False,
                        )
                        db.commit()
                        flash(
                            f"Collection {reference} recorded. Sale and lot are now COLLECTED.",
                            "success",
                        )
                        return redirect(url_for("sales.view", sale_id=sale["sale_id"]))
            except MySQLError as err:
                db.rollback()
                flash_db_error(err, "Could not record the collection.")
            except RuntimeError:
                flash("Cannot reach the database. Check MySQL and .env.", "danger")
    return render_template("collections/create.html", form=form, errors=errors, sales=sales)
