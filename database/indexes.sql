-- AgriAuction extra indexes
-- Load after schema.sql. Primary keys, UNIQUE keys and FOREIGN KEY indexes
-- already exist. This file only adds extra search/filter indexes.
--
-- MySQL 8.0 does not support CREATE INDEX IF NOT EXISTS. Run this file once.
-- Re-running it after the indexes exist will raise error 1061 (duplicate key name).
--
--   SOURCE C:/AgriAuction/database/indexes.sql;

USE agriauction;

-- Open lots by closing time (dashboard / close-auction work list)
CREATE INDEX idx_produce_lots_status_end
    ON produce_lots (status, auction_end);

-- A farmer's lots filtered by auction status
CREATE INDEX idx_produce_lots_farmer_status
    ON produce_lots (farmer_id, status);

-- Lots of one commodity filtered by status
CREATE INDEX idx_produce_lots_type_status
    ON produce_lots (produce_type_id, status);

-- Winner selection: highest VALID bid, earliest time as tie-breaker
CREATE INDEX idx_bids_winner_selection
    ON bids (lot_id, status, bid_amount, bid_time);

-- Sum verified payments for one sale
CREATE INDEX idx_payments_sale_status
    ON payments (sale_id, status);

-- Monthly sales reports
CREATE INDEX idx_sales_date
    ON successful_sales (sale_date);

-- Payment history by date
CREATE INDEX idx_payments_date
    ON payments (payment_date);
