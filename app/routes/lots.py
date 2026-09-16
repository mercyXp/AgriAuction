"""Produce lot registration, search, edit, and opening for auction."""

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.auth import role_required
from app.database import execute, query_all, query_one
from app.helpers import dt_local, next_lot_number, parse_date, parse_datetime, parse_decimal

lots_bp = Blueprint("lots", __name__, url_prefix="/lots")
LOT_ROLES = ("ADMIN", "OPERATOR", "AUCTION_CLERK")
EDIT_ROLES = ("ADMIN", "OPERATOR")

LOT_SELECT = """
    SELECT pl.*,
           CONCAT(f.first_name, ' ', f.last_name) AS farmer_name,
           f.farm_name,
           f.is_active AS farmer_active,
           pt.name AS produce_name,
           pt.unit_of_measure AS produce_unit,
           qg.grade_code,
           qg.grade_name,
           d.depot_name,
           d.location AS depot_location
    FROM produce_lots AS pl
    INNER JOIN farmers AS f ON f.farmer_id = pl.farmer_id
    INNER JOIN produce_types AS pt ON pt.produce_type_id = pl.produce_type_id
    INNER JOIN quality_grades AS qg ON qg.grade_id = pl.grade_id
    INNER JOIN depots AS d ON d.depot_id = pl.depot_id
"""


def _lookups(active_only=True):
    extra = "WHERE is_active = 1" if active_only else ""
    return {
        "farmers": query_all(
            f"SELECT farmer_id, farmer_code, first_name, last_name, farm_name "
            f"FROM farmers {extra} ORDER BY last_name, first_name",
            (),
        ),
        "produce_types": query_all(
            f"SELECT produce_type_id, name, unit_of_measure FROM produce_types {extra} ORDER BY name",
            (),
        ),
        "grades": query_all(
            f"SELECT grade_id, grade_code, grade_name FROM quality_grades {extra} ORDER BY grade_code",
            (),
        ),
        "depots": query_all(
            f"SELECT depot_id, depot_code, depot_name FROM depots {extra} ORDER BY depot_name",
            (),
        ),
    }


def _empty_form():
    return {
        "farmer_id": "",
        "produce_type_id": "",
        "grade_id": "",
        "depot_id": "",
        "quantity": "",
        "inspection_date": "",
        "auction_start": "",
        "auction_end": "",
        "minimum_bid_price": "",
    }


def validate_lot(form):
    errors = {}
    data = {
        "farmer_id": (form.get("farmer_id") or "").strip(),
        "produce_type_id": (form.get("produce_type_id") or "").strip(),
        "grade_id": (form.get("grade_id") or "").strip(),
        "depot_id": (form.get("depot_id") or "").strip(),
        "quantity": parse_decimal(form.get("quantity"), "quantity", errors, minimum=0),
        "inspection_date": parse_date(form.get("inspection_date"), "inspection_date", errors),
        "auction_start": parse_datetime(form.get("auction_start"), "auction_start", errors),
        "auction_end": parse_datetime(form.get("auction_end"), "auction_end", errors),
        "minimum_bid_price": parse_decimal(
            form.get("minimum_bid_price"), "minimum_bid_price", errors, minimum=0
        ),
    }
    for field, label in (
        ("farmer_id", "farmer"),
        ("produce_type_id", "produce type"),
        ("grade_id", "quality grade"),
        ("depot_id", "depot"),
    ):
        if not data[field].isdigit():
            errors[field] = f"Choose a {label}."

    if data["auction_start"] and data["auction_end"] and data["auction_end"] <= data["auction_start"]:
        errors["auction_end"] = "Auction end must be after auction start."

    if "farmer_id" not in errors:
        farmer = query_one(
            "SELECT is_active FROM farmers WHERE farmer_id = %s",
            (int(data["farmer_id"]),),
        )
        if farmer is None:
            errors["farmer_id"] = "Farmer not found."
        elif not farmer["is_active"]:
            errors["farmer_id"] = "Only an active farmer can register a lot."

    if "produce_type_id" not in errors:
        produce = query_one(
            "SELECT is_active, unit_of_measure FROM produce_types WHERE produce_type_id = %s",
            (int(data["produce_type_id"]),),
        )
        if produce is None:
            errors["produce_type_id"] = "Produce type not found."
        elif not produce["is_active"]:
            errors["produce_type_id"] = "That produce type is inactive."
        else:
            data["unit_of_measure"] = produce["unit_of_measure"]

    if "grade_id" not in errors:
        grade = query_one(
            "SELECT is_active FROM quality_grades WHERE grade_id = %s",
            (int(data["grade_id"]),),
        )
        if grade is None:
            errors["grade_id"] = "Quality grade not found."
        elif not grade["is_active"]:
            errors["grade_id"] = "That quality grade is inactive."

    if "depot_id" not in errors:
        depot = query_one(
            "SELECT is_active FROM depots WHERE depot_id = %s",
            (int(data["depot_id"]),),
        )
        if depot is None:
            errors["depot_id"] = "Depot not found."
        elif not depot["is_active"]:
            errors["depot_id"] = "That depot is inactive."

    return data, errors


@lots_bp.route("/")
@role_required(*LOT_ROLES)
def index():
    q = (request.args.get("q") or "").strip()
    status = request.args.get("status") or "all"
    like = f"%{q}%"
    extra = "AND pl.status = %s" if status != "all" else ""
    params = [q, like, like, like, like]
    if status != "all":
        params.append(status)
    try:
        lots = query_all(
            f"""
            {LOT_SELECT}
            WHERE (%s = '' OR pl.lot_number LIKE %s OR f.last_name LIKE %s
                   OR f.farm_name LIKE %s OR pt.name LIKE %s)
            {extra}
            ORDER BY pl.auction_start DESC, pl.lot_number
            """,
            tuple(params),
        )
    except RuntimeError:
        flash("Cannot reach the database. Check MySQL and .env.", "danger")
        lots = []
    return render_template("lots/index.html", lots=lots, q=q, status=status)


@lots_bp.route("/create", methods=["GET", "POST"])
@role_required(*EDIT_ROLES)
def create():
    form = _empty_form()
    errors = {}
    lookups = _lookups(active_only=True)
    if request.method == "POST":
        data, errors = validate_lot(request.form)
        form = {
            "farmer_id": request.form.get("farmer_id", ""),
            "produce_type_id": request.form.get("produce_type_id", ""),
            "grade_id": request.form.get("grade_id", ""),
            "depot_id": request.form.get("depot_id", ""),
            "quantity": request.form.get("quantity", ""),
            "inspection_date": request.form.get("inspection_date", ""),
            "auction_start": request.form.get("auction_start", ""),
            "auction_end": request.form.get("auction_end", ""),
            "minimum_bid_price": request.form.get("minimum_bid_price", ""),
        }
        if not errors:
            code = next_lot_number()
            lot_id, _ = execute(
                """
                INSERT INTO produce_lots (
                    lot_number, farmer_id, produce_type_id, grade_id, depot_id,
                    quantity, unit_of_measure, inspection_date, auction_start,
                    auction_end, minimum_bid_price, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'REGISTERED')
                """,
                (
                    code,
                    int(data["farmer_id"]),
                    int(data["produce_type_id"]),
                    int(data["grade_id"]),
                    int(data["depot_id"]),
                    data["quantity"],
                    data["unit_of_measure"],
                    data["inspection_date"],
                    data["auction_start"],
                    data["auction_end"],
                    data["minimum_bid_price"],
                ),
            )
            flash(f"Lot {code} was registered. Open it when the auction should start.", "success")
            return redirect(url_for("lots.view", lot_id=lot_id))
    return render_template("lots/create.html", form=form, errors=errors, lookups=lookups)


@lots_bp.route("/<int:lot_id>")
@role_required(*LOT_ROLES)
def view(lot_id):
    lot = query_one(f"{LOT_SELECT} WHERE pl.lot_id = %s", (lot_id,))
    if lot is None:
        flash("Lot not found.", "warning")
        return redirect(url_for("lots.index"))
    bids = query_all(
        """
        SELECT b.bid_id, b.bid_amount, b.bid_time, b.status,
               byr.buyer_code, byr.business_name
        FROM bids AS b
        INNER JOIN buyers AS byr ON byr.buyer_id = b.buyer_id
        WHERE b.lot_id = %s
        ORDER BY b.bid_amount DESC, b.bid_time ASC
        """,
        (lot_id,),
    )
    high = query_one(
        """
        SELECT MAX(bid_amount) AS highest
        FROM bids
        WHERE lot_id = %s AND status IN ('VALID', 'WINNING')
        """,
        (lot_id,),
    )
    return render_template(
        "lots/view.html",
        lot=lot,
        bids=bids,
        highest=high["highest"] if high else None,
        now=datetime.now(),
    )


@lots_bp.route("/<int:lot_id>/edit", methods=["GET", "POST"])
@role_required(*EDIT_ROLES)
def edit(lot_id):
    lot = query_one("SELECT * FROM produce_lots WHERE lot_id = %s", (lot_id,))
    if lot is None:
        flash("Lot not found.", "warning")
        return redirect(url_for("lots.index"))
    if lot["status"] != "REGISTERED":
        flash("Only a REGISTERED lot can be edited.", "warning")
        return redirect(url_for("lots.view", lot_id=lot_id))
    form = {
        "farmer_id": str(lot["farmer_id"]),
        "produce_type_id": str(lot["produce_type_id"]),
        "grade_id": str(lot["grade_id"]),
        "depot_id": str(lot["depot_id"]),
        "quantity": str(lot["quantity"]),
        "inspection_date": lot["inspection_date"].isoformat()
        if hasattr(lot["inspection_date"], "isoformat")
        else str(lot["inspection_date"]),
        "auction_start": dt_local(lot["auction_start"]),
        "auction_end": dt_local(lot["auction_end"]),
        "minimum_bid_price": str(lot["minimum_bid_price"]),
    }
    errors = {}
    lookups = _lookups(active_only=True)
    if request.method == "POST":
        data, errors = validate_lot(request.form)
        form = {
            "farmer_id": request.form.get("farmer_id", ""),
            "produce_type_id": request.form.get("produce_type_id", ""),
            "grade_id": request.form.get("grade_id", ""),
            "depot_id": request.form.get("depot_id", ""),
            "quantity": request.form.get("quantity", ""),
            "inspection_date": request.form.get("inspection_date", ""),
            "auction_start": request.form.get("auction_start", ""),
            "auction_end": request.form.get("auction_end", ""),
            "minimum_bid_price": request.form.get("minimum_bid_price", ""),
        }
        if not errors:
            execute(
                """
                UPDATE produce_lots
                SET farmer_id = %s, produce_type_id = %s, grade_id = %s, depot_id = %s,
                    quantity = %s, unit_of_measure = %s, inspection_date = %s,
                    auction_start = %s, auction_end = %s, minimum_bid_price = %s
                WHERE lot_id = %s AND status = 'REGISTERED'
                """,
                (
                    int(data["farmer_id"]),
                    int(data["produce_type_id"]),
                    int(data["grade_id"]),
                    int(data["depot_id"]),
                    data["quantity"],
                    data["unit_of_measure"],
                    data["inspection_date"],
                    data["auction_start"],
                    data["auction_end"],
                    data["minimum_bid_price"],
                    lot_id,
                ),
            )
            flash("Lot details were updated.", "success")
            return redirect(url_for("lots.view", lot_id=lot_id))
    return render_template("lots/edit.html", lot=lot, form=form, errors=errors, lookups=lookups)


@lots_bp.route("/<int:lot_id>/open", methods=["POST"])
@role_required("ADMIN", "AUCTION_CLERK")
def open_auction(lot_id):
    lot = query_one("SELECT * FROM produce_lots WHERE lot_id = %s", (lot_id,))
    if lot is None:
        flash("Lot not found.", "warning")
        return redirect(url_for("lots.index"))
    if lot["status"] != "REGISTERED":
        flash("Only a REGISTERED lot can be opened for bidding.", "danger")
        return redirect(url_for("lots.view", lot_id=lot_id))
    if lot["auction_end"] <= datetime.now():
        flash("This auction window has already ended. Update the end time first.", "danger")
        return redirect(url_for("lots.view", lot_id=lot_id))
    execute(
        "UPDATE produce_lots SET status = 'OPEN' WHERE lot_id = %s AND status = 'REGISTERED'",
        (lot_id,),
    )
    flash(f"{lot['lot_number']} is now OPEN for bids.", "success")
    return redirect(url_for("lots.view", lot_id=lot_id))
