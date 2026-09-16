"""Staff-placed bids on OPEN lots. Buyers do not log in; clerks record their offers."""

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.auth import role_required
from app.database import MySQLError, execute, get_db, query_all, query_one
from app.helpers import flash_db_error, parse_decimal
from app.utils import format_zmw

bids_bp = Blueprint("bids", __name__, url_prefix="/bids")
TRADE_ROLES = ("ADMIN", "AUCTION_CLERK")


def validate_bid(lot, buyer, amount, now):
    """Server-side rules that also exist as CHECKs / procedure logic."""
    if buyer is None:
        return "Buyer not found."
    if not buyer["is_active"]:
        return "That buyer is inactive and cannot bid."
    if lot is None:
        return "Lot not found."
    if lot["status"] != "OPEN":
        if lot["status"] in ("CLOSED", "SOLD", "UNSOLD", "COLLECTED"):
            return "This auction is already closed."
        return "Bids are only accepted on OPEN lots."
    if now >= lot["auction_end"]:
        return "This auction has ended. No further bids can be placed."
    if amount is None:
        return "Enter a bid amount."
    if amount < lot["minimum_bid_price"]:
        return (
            f"Bid amount must be at least {format_zmw(lot['minimum_bid_price'])}."
        )
    return None


@bids_bp.route("/")
@role_required(*TRADE_ROLES)
def index():
    q = (request.args.get("q") or "").strip()
    like = f"%{q}%"
    try:
        bids = query_all(
            """
            SELECT b.bid_id, b.bid_amount, b.bid_time, b.status,
                   pl.lot_id, pl.lot_number, pl.status AS lot_status,
                   byr.buyer_code, byr.business_name
            FROM bids AS b
            INNER JOIN produce_lots AS pl ON pl.lot_id = b.lot_id
            INNER JOIN buyers AS byr ON byr.buyer_id = b.buyer_id
            WHERE (%s = '' OR pl.lot_number LIKE %s OR byr.business_name LIKE %s
                   OR byr.buyer_code LIKE %s)
            ORDER BY b.bid_time DESC
            LIMIT 200
            """,
            (q, like, like, like),
        )
        open_lots = query_all(
            """
            SELECT lot_id, lot_number, minimum_bid_price, auction_end
            FROM produce_lots
            WHERE status = 'OPEN'
            ORDER BY auction_end
            """,
            (),
        )
    except RuntimeError:
        flash("Cannot reach the database. Check MySQL and .env.", "danger")
        bids = []
        open_lots = []
    return render_template("bids/index.html", bids=bids, open_lots=open_lots, q=q)


@bids_bp.route("/create", methods=["GET", "POST"])
@role_required(*TRADE_ROLES)
def create():
    selected_lot = request.args.get("lot_id") or request.form.get("lot_id") or ""
    form = {
        "lot_id": str(selected_lot),
        "buyer_id": request.form.get("buyer_id", ""),
        "bid_amount": request.form.get("bid_amount", ""),
    }
    error = None
    open_lots = query_all(
        """
        SELECT lot_id, lot_number, minimum_bid_price, auction_end, unit_of_measure
        FROM produce_lots
        WHERE status = 'OPEN'
        ORDER BY auction_end
        """,
        (),
    )
    buyers = query_all(
        """
        SELECT buyer_id, buyer_code, business_name
        FROM buyers
        WHERE is_active = 1
        ORDER BY business_name
        """,
        (),
    )
    if request.method == "POST":
        errors = {}
        amount = parse_decimal(form["bid_amount"], "bid_amount", errors, minimum=0)
        if errors:
            error = errors.get("bid_amount")
        elif not str(form["lot_id"]).isdigit():
            error = "Choose an OPEN lot."
        elif not str(form["buyer_id"]).isdigit():
            error = "Choose an active buyer."
        else:
            db = get_db()
            try:
                # Lock the lot so a concurrent close cannot race the insert.
                lot = query_one(
                    """
                    SELECT lot_id, status, minimum_bid_price, auction_end
                    FROM produce_lots
                    WHERE lot_id = %s
                    FOR UPDATE
                    """,
                    (int(form["lot_id"]),),
                )
                buyer = query_one(
                    "SELECT buyer_id, is_active FROM buyers WHERE buyer_id = %s",
                    (int(form["buyer_id"]),),
                )
                error = validate_bid(lot, buyer, amount, datetime.now())
                if error:
                    db.rollback()
                else:
                    execute(
                        """
                        INSERT INTO bids (lot_id, buyer_id, bid_amount, bid_time, status)
                        VALUES (%s, %s, %s, NOW(), 'VALID')
                        """,
                        (int(form["lot_id"]), int(form["buyer_id"]), amount),
                        commit=False,
                    )
                    db.commit()
                    flash("Bid recorded.", "success")
                    return redirect(url_for("lots.view", lot_id=int(form["lot_id"])))
            except MySQLError as err:
                db.rollback()
                flash_db_error(err, "Could not record the bid.")
            except RuntimeError:
                flash("Cannot reach the database. Check MySQL and .env.", "danger")
    return render_template(
        "bids/create.html",
        form=form,
        error=error,
        open_lots=open_lots,
        buyers=buyers,
    )
