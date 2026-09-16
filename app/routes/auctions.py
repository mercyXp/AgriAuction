"""Close OPEN auctions by calling sp_close_auction (atomic, row-locked)."""

from flask import Blueprint, flash, redirect, render_template, url_for

from app.auth import role_required
from app.database import MySQLError, callproc, query_all, query_one
from app.helpers import flash_db_error

auctions_bp = Blueprint("auctions", __name__, url_prefix="/auctions")
TRADE_ROLES = ("ADMIN", "AUCTION_CLERK")


@auctions_bp.route("/")
@role_required(*TRADE_ROLES)
def index():
    try:
        open_lots = query_all(
            """
            SELECT *
            FROM vw_auction_lot_summary
            WHERE auction_status = 'OPEN'
            ORDER BY auction_end
            """,
            (),
        )
        recent = query_all(
            """
            SELECT *
            FROM vw_auction_lot_summary
            WHERE auction_status IN ('SOLD', 'UNSOLD', 'COLLECTED')
            ORDER BY lot_number DESC
            LIMIT 20
            """,
            (),
        )
    except RuntimeError:
        flash("Cannot reach the database. Check MySQL and .env.", "danger")
        open_lots = []
        recent = []
    return render_template("auctions/index.html", open_lots=open_lots, recent=recent)


@auctions_bp.route("/<int:lot_id>/close", methods=["POST"])
@role_required(*TRADE_ROLES)
def close(lot_id):
    lot = query_one(
        "SELECT lot_id, lot_number, status FROM produce_lots WHERE lot_id = %s",
        (lot_id,),
    )
    if lot is None:
        flash("Lot not found.", "warning")
        return redirect(url_for("auctions.index"))
    if lot["status"] == "SOLD":
        flash("This produce lot has already been sold.", "danger")
        return redirect(url_for("lots.view", lot_id=lot_id))
    if lot["status"] != "OPEN":
        flash("This auction is already closed.", "danger")
        return redirect(url_for("lots.view", lot_id=lot_id))
    try:
        rows = callproc("sp_close_auction", (lot_id,))
    except MySQLError as err:
        flash_db_error(err, "Could not close the auction.")
        return redirect(url_for("lots.view", lot_id=lot_id))
    except RuntimeError:
        flash("Cannot reach the database. Check MySQL and .env.", "danger")
        return redirect(url_for("auctions.index"))

    result = rows[0] if rows else {}
    message = result.get("message") or "Auction closed."
    if result.get("lot_status") == "UNSOLD":
        flash("Auction closed — no winner", "warning")
    else:
        flash(message, "success")
    return redirect(url_for("auctions.result", lot_id=lot_id))


@auctions_bp.route("/<int:lot_id>/result")
@role_required(*TRADE_ROLES)
def result(lot_id):
    lot = query_one(
        """
        SELECT pl.*, pt.name AS produce_name,
               CONCAT(f.first_name, ' ', f.last_name) AS farmer_name
        FROM produce_lots AS pl
        INNER JOIN produce_types AS pt ON pt.produce_type_id = pl.produce_type_id
        INNER JOIN farmers AS f ON f.farmer_id = pl.farmer_id
        WHERE pl.lot_id = %s
        """,
        (lot_id,),
    )
    if lot is None:
        flash("Lot not found.", "warning")
        return redirect(url_for("auctions.index"))
    sale = query_one(
        """
        SELECT s.*, byr.business_name, byr.buyer_code,
               b.bid_amount, b.bid_time
        FROM successful_sales AS s
        INNER JOIN buyers AS byr ON byr.buyer_id = s.buyer_id
        INNER JOIN bids AS b ON b.bid_id = s.winning_bid_id
        WHERE s.lot_id = %s
        """,
        (lot_id,),
    )
    return render_template("auctions/result.html", lot=lot, sale=sale)
