-- AgriAuction stored procedures
-- Load after schema.sql:
--   SOURCE C:/AgriAuction/database/procedures.sql;
--
-- Workbench: execute this whole file. DELIMITER is required so ; inside
-- the procedure body is not treated as the end of the CREATE statement.

USE agriauction;

DROP PROCEDURE IF EXISTS sp_close_auction;
DROP PROCEDURE IF EXISTS sp_record_payment;

DELIMITER $$

-- -----------------------------------------------------------------------------
-- sp_close_auction
-- Atomic close of one OPEN lot.
-- Highest VALID bid wins. Equal amounts: earliest bid_time wins.
-- No valid bid: lot becomes UNSOLD. Winner: lot SOLD + one successful_sales row.
-- UNIQUE (lot_id) on successful_sales is the final guard against two sales.
-- -----------------------------------------------------------------------------
CREATE PROCEDURE sp_close_auction(IN p_lot_id INT UNSIGNED)
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_min_bid DECIMAL(12, 2);
    DECLARE v_bid_id INT UNSIGNED;
    DECLARE v_buyer_id INT UNSIGNED;
    DECLARE v_amount DECIMAL(12, 2);
    DECLARE v_sale_ref VARCHAR(40);
    DECLARE v_bid_count INT DEFAULT 0;
    DECLARE v_no_row TINYINT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    DECLARE CONTINUE HANDLER FOR NOT FOUND
    BEGIN
        SET v_no_row = 1;
    END;

    START TRANSACTION;

    SET v_no_row = 0;

    -- Lock the lot so two clerks cannot close it at the same time.
    SELECT status, minimum_bid_price
    INTO v_status, v_min_bid
    FROM produce_lots
    WHERE lot_id = p_lot_id
    FOR UPDATE;

    IF v_no_row = 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Lot not found.';
    END IF;

    IF v_status <> 'OPEN' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only an OPEN lot can be closed.';
    END IF;

    -- Lock every bid on this lot, then pick the winner.
    -- COUNT(*) ... FOR UPDATE locks matching rows without returning a result set.
    SELECT COUNT(*)
    INTO v_bid_count
    FROM bids
    WHERE lot_id = p_lot_id
    FOR UPDATE;

    SET v_no_row = 0;
    SET v_bid_id = NULL;
    SET v_buyer_id = NULL;
    SET v_amount = NULL;

    SELECT bid_id, buyer_id, bid_amount
    INTO v_bid_id, v_buyer_id, v_amount
    FROM bids
    WHERE lot_id = p_lot_id
      AND status = 'VALID'
      AND bid_amount >= v_min_bid
    ORDER BY bid_amount DESC, bid_time ASC
    LIMIT 1;

    IF v_no_row = 1 OR v_bid_id IS NULL THEN
        UPDATE produce_lots
        SET status = 'UNSOLD'
        WHERE lot_id = p_lot_id;

        COMMIT;

        SELECT
            p_lot_id AS lot_id,
            'UNSOLD' AS lot_status,
            NULL AS winning_bid_id,
            NULL AS buyer_id,
            NULL AS sale_amount,
            NULL AS sale_reference,
            'Auction closed — no winner' AS message;
    ELSE
        UPDATE bids
        SET status = 'WINNING'
        WHERE bid_id = v_bid_id;

        SET v_sale_ref = CONCAT(
            'SAL-',
            DATE_FORMAT(NOW(), '%Y%m%d%H%i%s'),
            '-',
            p_lot_id
        );

        INSERT INTO successful_sales (
            sale_reference,
            lot_id,
            winning_bid_id,
            buyer_id,
            sale_amount,
            sale_date,
            status
        ) VALUES (
            v_sale_ref,
            p_lot_id,
            v_bid_id,
            v_buyer_id,
            v_amount,
            NOW(),
            'PAYMENT_PENDING'
        );

        UPDATE produce_lots
        SET status = 'SOLD'
        WHERE lot_id = p_lot_id;

        COMMIT;

        SELECT
            p_lot_id AS lot_id,
            'SOLD' AS lot_status,
            v_bid_id AS winning_bid_id,
            v_buyer_id AS buyer_id,
            v_amount AS sale_amount,
            v_sale_ref AS sale_reference,
            'Auction closed — winner recorded' AS message;
    END IF;
END$$

-- -----------------------------------------------------------------------------
-- sp_record_payment
-- Records one payment. VERIFIED amounts cannot push the sale over sale_amount.
-- Sale status is recalculated from verified totals only.
-- -----------------------------------------------------------------------------
CREATE PROCEDURE sp_record_payment(
    IN p_sale_id INT UNSIGNED,
    IN p_amount DECIMAL(12, 2),
    IN p_payment_reference VARCHAR(40),
    IN p_payment_method VARCHAR(20),
    IN p_payment_date DATETIME,
    IN p_recorded_by INT UNSIGNED,
    IN p_status VARCHAR(20)
)
BEGIN
    DECLARE v_sale_status VARCHAR(20);
    DECLARE v_sale_amount DECIMAL(12, 2);
    DECLARE v_verified_total DECIMAL(12, 2);
    DECLARE v_new_status VARCHAR(20);
    DECLARE v_no_row TINYINT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    DECLARE CONTINUE HANDLER FOR NOT FOUND
    BEGIN
        SET v_no_row = 1;
    END;

    START TRANSACTION;

    SET v_no_row = 0;

    SELECT status, sale_amount
    INTO v_sale_status, v_sale_amount
    FROM successful_sales
    WHERE sale_id = p_sale_id
    FOR UPDATE;

    IF v_no_row = 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Sale not found.';
    END IF;

    IF v_sale_status IN ('CANCELLED', 'COLLECTED') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Payments cannot be recorded for this sale.';
    END IF;

    IF p_amount IS NULL OR p_amount <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Payment amount must be greater than zero.';
    END IF;

    IF p_payment_method NOT IN ('BANK_TRANSFER', 'CASH', 'MOBILE_MONEY') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid payment method.';
    END IF;

    IF p_status NOT IN ('PENDING', 'VERIFIED', 'REJECTED') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid payment status.';
    END IF;

    SELECT COALESCE(SUM(amount), 0)
    INTO v_verified_total
    FROM payments
    WHERE sale_id = p_sale_id
      AND status = 'VERIFIED';

    IF p_status = 'VERIFIED' AND (v_verified_total + p_amount) > v_sale_amount THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Payment exceeds the outstanding balance.';
    END IF;

    INSERT INTO payments (
        sale_id,
        payment_reference,
        amount,
        payment_method,
        payment_date,
        status,
        recorded_by
    ) VALUES (
        p_sale_id,
        p_payment_reference,
        p_amount,
        p_payment_method,
        p_payment_date,
        p_status,
        p_recorded_by
    );

    SELECT COALESCE(SUM(amount), 0)
    INTO v_verified_total
    FROM payments
    WHERE sale_id = p_sale_id
      AND status = 'VERIFIED';

    IF v_verified_total <= 0 THEN
        SET v_new_status = 'PAYMENT_PENDING';
    ELSEIF v_verified_total < v_sale_amount THEN
        SET v_new_status = 'PARTIALLY_PAID';
    ELSE
        SET v_new_status = 'PAID';
    END IF;

    UPDATE successful_sales
    SET status = v_new_status
    WHERE sale_id = p_sale_id;

    COMMIT;

    SELECT
        p_sale_id AS sale_id,
        v_new_status AS sale_status,
        v_sale_amount AS sale_amount,
        v_verified_total AS total_verified_payments,
        (v_sale_amount - v_verified_total) AS outstanding_balance,
        'Payment recorded' AS message;
END$$

DELIMITER ;
