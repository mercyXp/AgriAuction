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
