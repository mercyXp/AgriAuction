-- AgriAuction views
-- Load after schema.sql (and seed.sql if you want to query immediately):
--   SOURCE C:/AgriAuction/database/views.sql;

USE agriauction;

-- -----------------------------------------------------------------------------
-- vw_auction_lot_summary
-- One row per lot: who supplied it, what it is, where it is, and bidding activity.
-- LEFT JOIN bids so lots with zero bids still appear.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_auction_lot_summary AS
SELECT
    pl.lot_id,
    pl.lot_number,
    CONCAT(f.first_name, ' ', f.last_name) AS farmer,
    f.farm_name,
    pt.name AS produce_type,
    qg.grade_name AS quality_grade,
    d.depot_name AS depot,
    d.location AS depot_location,
    pl.quantity,
    pl.unit_of_measure,
    pl.minimum_bid_price AS minimum_bid,
    pl.auction_end,
    pl.status AS auction_status,
    COUNT(b.bid_id) AS number_of_bids,
    MAX(CASE
            WHEN b.status IN ('VALID', 'WINNING') THEN b.bid_amount
            ELSE NULL
        END) AS highest_bid
FROM produce_lots AS pl
INNER JOIN farmers AS f
    ON f.farmer_id = pl.farmer_id
INNER JOIN produce_types AS pt
    ON pt.produce_type_id = pl.produce_type_id
INNER JOIN quality_grades AS qg
    ON qg.grade_id = pl.grade_id
INNER JOIN depots AS d
    ON d.depot_id = pl.depot_id
LEFT JOIN bids AS b
    ON b.lot_id = pl.lot_id
GROUP BY
    pl.lot_id,
    pl.lot_number,
    f.first_name,
    f.last_name,
    f.farm_name,
    pt.name,
    qg.grade_name,
    d.depot_name,
    d.location,
    pl.quantity,
    pl.unit_of_measure,
    pl.minimum_bid_price,
    pl.auction_end,
    pl.status;

-- -----------------------------------------------------------------------------
-- vw_sales_payment_summary
-- Outstanding balance uses VERIFIED payments only.
-- PENDING and REJECTED amounts do not reduce what the buyer still owes.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_sales_payment_summary AS
SELECT
    s.sale_id,
    s.sale_reference,
    pl.lot_number AS lot,
    byr.business_name AS buyer,
    s.sale_amount,
    COALESCE(SUM(CASE
                     WHEN p.status = 'VERIFIED' THEN p.amount
                     ELSE 0
                 END), 0) AS total_verified_payments,
    (s.sale_amount - COALESCE(SUM(CASE
                                      WHEN p.status = 'VERIFIED' THEN p.amount
                                      ELSE 0
                                  END), 0)) AS outstanding_balance,
    s.status AS sale_status
FROM successful_sales AS s
INNER JOIN produce_lots AS pl
    ON pl.lot_id = s.lot_id
INNER JOIN buyers AS byr
    ON byr.buyer_id = s.buyer_id
LEFT JOIN payments AS p
    ON p.sale_id = s.sale_id
GROUP BY
    s.sale_id,
    s.sale_reference,
    pl.lot_number,
    byr.business_name,
    s.sale_amount,
    s.status;
