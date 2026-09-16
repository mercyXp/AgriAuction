-- AgriAuction Phase 5 queries
-- Run after schema.sql, seed.sql, views.sql, procedures.sql and indexes.sql.
-- These statements are for demonstration. CALL examples that change data are
-- commented so seed OPEN lots stay available until you choose to close them.

USE agriauction;

-- -----------------------------------------------------------------------------
-- Views
-- -----------------------------------------------------------------------------

-- All lots with bid counts and current high bid
SELECT *
FROM vw_auction_lot_summary
ORDER BY lot_number;

-- Lots that are still receiving bids
SELECT lot_number, farmer, produce_type, minimum_bid, number_of_bids, highest_bid, auction_end
FROM vw_auction_lot_summary
WHERE auction_status = 'OPEN'
ORDER BY auction_end;

-- Sales with how much is still outstanding (ZMW)
SELECT
    sale_reference,
    lot,
    buyer,
    sale_amount,
    total_verified_payments,
    outstanding_balance,
    sale_status
FROM vw_sales_payment_summary
ORDER BY outstanding_balance DESC;

-- -----------------------------------------------------------------------------
-- EXPLAIN — confirm extra indexes can be used
-- -----------------------------------------------------------------------------

EXPLAIN
SELECT lot_id, lot_number, auction_end
FROM produce_lots
WHERE status = 'OPEN'
ORDER BY auction_end;

EXPLAIN
SELECT bid_id, buyer_id, bid_amount, bid_time
FROM bids
WHERE lot_id = 16
  AND status = 'VALID'
ORDER BY bid_amount DESC, bid_time ASC
LIMIT 1;

EXPLAIN
SELECT COALESCE(SUM(amount), 0) AS verified_total
FROM payments
WHERE sale_id = 8
  AND status = 'VERIFIED';

-- -----------------------------------------------------------------------------
-- Procedure calls (commented: they write data)
-- -----------------------------------------------------------------------------

-- Close an OPEN seed lot (lot 16 currently has valid bids → should SOLD):
-- CALL sp_close_auction(16);

-- Close a lot with no valid bids (create a test OPEN lot first, or use a copy):
-- CALL sp_close_auction(13);  -- will fail: status is UNSOLD, not OPEN

-- Record a verified payment against a pending sale (sale 11 amount 5900):
-- CALL sp_record_payment(
--     11,
--     5900.00,
--     'PAY-DEMO-001',
--     'BANK_TRANSFER',
--     NOW(),
--     4,
--     'VERIFIED'
-- );

-- This should fail: verified payments on sale 6 already equal 4450.00
-- CALL sp_record_payment(
--     6,
--     1.00,
--     'PAY-DEMO-OVER',
--     'CASH',
--     NOW(),
--     4,
--     'VERIFIED'
-- );

-- =============================================================================
-- Phase 21 — labelled SQL demonstrations (business-purpose queries)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- DDL examples (already applied by schema.sql / indexes.sql)
-- -----------------------------------------------------------------------------
-- CREATE TABLE: see database/schema.sql (staff, farmers, produce_lots, ...)
-- CREATE INDEX: see database/indexes.sql
-- ALTER TABLE example (do not run against the live project unless needed):
-- ALTER TABLE buyers ADD COLUMN notes VARCHAR(255) NULL;
-- Revert would be: ALTER TABLE buyers DROP COLUMN notes;

-- -----------------------------------------------------------------------------
-- DML
-- -----------------------------------------------------------------------------

-- INSERT: a new pending payment is normally done by CALL sp_record_payment.
-- Direct INSERT is shown here only as DML syntax:
-- INSERT INTO quality_grades (grade_code, grade_name, description, is_active)
-- VALUES ('DEMO', 'Demonstration grade', 'Viva-only example', 0);

-- UPDATE: deactivate rather than delete a farmer who still has lots
-- UPDATE farmers
-- SET is_active = 0
-- WHERE farmer_code = 'FRM-0012'
--   AND is_active = 1;

-- DELETE: only safe for rows with no history. The application deactivates instead.
-- DELETE FROM produce_types WHERE name = 'Does-Not-Exist';

-- -----------------------------------------------------------------------------
-- SELECT — filtering, sorting, LIKE, BETWEEN, IN, IS NULL
-- -----------------------------------------------------------------------------

SELECT farmer_code, first_name, last_name, farm_name
FROM farmers
WHERE is_active = 1
ORDER BY last_name, first_name;

SELECT lot_number, status, minimum_bid_price
FROM produce_lots
WHERE status IN ('OPEN', 'REGISTERED')
ORDER BY auction_start;

SELECT buyer_code, business_name, email
FROM buyers
WHERE email IS NULL
ORDER BY business_name;

SELECT lot_number, auction_start, auction_end
FROM produce_lots
WHERE auction_start BETWEEN '2026-09-01' AND '2026-09-30'
ORDER BY auction_start;

SELECT farmer_code, farm_name, phone
FROM farmers
WHERE farm_name LIKE '%Farm%'
   OR last_name LIKE 'P%'
ORDER BY farm_name;

-- -----------------------------------------------------------------------------
-- Aggregates: COUNT, SUM, AVG, MIN, MAX
-- -----------------------------------------------------------------------------

SELECT
    COUNT(*) AS lots,
    SUM(quantity) AS total_qty,
    AVG(minimum_bid_price) AS avg_min_bid,
    MIN(minimum_bid_price) AS lowest_min_bid,
    MAX(minimum_bid_price) AS highest_min_bid
FROM produce_lots;

-- -----------------------------------------------------------------------------
-- GROUP BY
-- -----------------------------------------------------------------------------

SELECT pt.name AS produce_type, COUNT(pl.lot_id) AS lots, SUM(pl.quantity) AS tonnes
FROM produce_types AS pt
INNER JOIN produce_lots AS pl ON pl.produce_type_id = pt.produce_type_id
GROUP BY pt.produce_type_id, pt.name
ORDER BY tonnes DESC;

-- -----------------------------------------------------------------------------
-- INNER JOIN (lot + farmer + produce + depot)
-- -----------------------------------------------------------------------------

SELECT
    pl.lot_number,
    CONCAT(f.first_name, ' ', f.last_name) AS farmer,
    pt.name AS produce_type,
    d.depot_name,
    pl.status
FROM produce_lots AS pl
INNER JOIN farmers AS f ON f.farmer_id = pl.farmer_id
INNER JOIN produce_types AS pt ON pt.produce_type_id = pl.produce_type_id
INNER JOIN depots AS d ON d.depot_id = pl.depot_id
WHERE pl.status = 'SOLD'
ORDER BY pl.lot_number;

-- -----------------------------------------------------------------------------
-- LEFT JOIN (buyers with or without purchases)
-- -----------------------------------------------------------------------------

SELECT
    byr.buyer_code,
    byr.business_name,
    COUNT(s.sale_id) AS purchases,
    COALESCE(SUM(s.sale_amount), 0) AS total_spent
FROM buyers AS byr
LEFT JOIN successful_sales AS s ON s.buyer_id = byr.buyer_id
GROUP BY byr.buyer_id, byr.buyer_code, byr.business_name
ORDER BY total_spent DESC, byr.business_name;

-- -----------------------------------------------------------------------------
-- Subquery: buyers whose total purchases exceed the average buyer total
-- -----------------------------------------------------------------------------

SELECT byr.buyer_code, byr.business_name, totals.spent
FROM buyers AS byr
INNER JOIN (
    SELECT buyer_id, SUM(sale_amount) AS spent
    FROM successful_sales
    GROUP BY buyer_id
) AS totals ON totals.buyer_id = byr.buyer_id
WHERE totals.spent > (
    SELECT AVG(buyer_total)
    FROM (
        SELECT SUM(sale_amount) AS buyer_total
        FROM successful_sales
        GROUP BY buyer_id
    ) AS per_buyer
)
ORDER BY totals.spent DESC;

