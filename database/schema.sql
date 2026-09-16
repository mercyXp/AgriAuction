-- AgriAuction Digital Produce Trading Platform
-- Phase 2: MySQL 8 schema
--
-- This file creates the database and all core tables.
-- Load it in MySQL Workbench or from the command line:
--   mysql -u root -p < database/schema.sql
--
-- Table order matters: parent tables are created before child tables
-- so that FOREIGN KEY references are valid.

CREATE DATABASE IF NOT EXISTS agriauction
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE agriauction;

-- -----------------------------------------------------------------------------
-- 1. STAFF
-- Application users who log into the web system.
-- This is NOT a MySQL database account. MySQL users are created later.
-- -----------------------------------------------------------------------------
CREATE TABLE staff (
    staff_id        INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    username        VARCHAR(80)     NOT NULL,
    email           VARCHAR(120)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    first_name      VARCHAR(80)     NOT NULL,
    last_name       VARCHAR(80)     NOT NULL,
    role            ENUM(
                        'ADMIN',
                        'OPERATOR',
                        'AUCTION_CLERK',
                        'FINANCE',
                        'VIEWER'
                    )               NOT NULL,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (staff_id),
    UNIQUE KEY uq_staff_username (username),
    UNIQUE KEY uq_staff_email (email),
    CONSTRAINT chk_staff_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB COMMENT='Staff accounts used for application login and role-based access';

-- -----------------------------------------------------------------------------
-- 2. FARMERS
-- Registered producers who can have produce lots.
-- -----------------------------------------------------------------------------
CREATE TABLE farmers (
    farmer_id           INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    farmer_code         VARCHAR(20)     NOT NULL,
    first_name          VARCHAR(80)     NOT NULL,
    last_name           VARCHAR(80)     NOT NULL,
    phone               VARCHAR(20)     NOT NULL,
    email               VARCHAR(120)    NULL,
    address             VARCHAR(255)    NOT NULL,
    farm_name           VARCHAR(120)    NOT NULL,
    registration_date   DATE            NOT NULL,
    is_active           TINYINT(1)      NOT NULL DEFAULT 1,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (farmer_id),
    UNIQUE KEY uq_farmers_code (farmer_code),
    KEY idx_farmers_name (last_name, first_name),
    KEY idx_farmers_active (is_active),
    CONSTRAINT chk_farmers_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB COMMENT='Farmers who register agricultural produce for auction';

-- -----------------------------------------------------------------------------
-- 3. BUYERS
-- Registered buyers who may place bids on open lots.
-- -----------------------------------------------------------------------------
CREATE TABLE buyers (
    buyer_id            INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    buyer_code          VARCHAR(20)     NOT NULL,
    business_name       VARCHAR(150)    NOT NULL,
    contact_person      VARCHAR(120)    NOT NULL,
    phone               VARCHAR(20)     NOT NULL,
    email               VARCHAR(120)    NULL,
    address             VARCHAR(255)    NOT NULL,
    registration_date   DATE            NOT NULL,
    is_active           TINYINT(1)      NOT NULL DEFAULT 1,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (buyer_id),
    UNIQUE KEY uq_buyers_code (buyer_code),
    KEY idx_buyers_business_name (business_name),
    KEY idx_buyers_active (is_active),
    CONSTRAINT chk_buyers_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB COMMENT='Registered buyers who bid on open produce lots';

-- -----------------------------------------------------------------------------
-- 4. PRODUCE_TYPES
-- Lookup table for commodities such as maize, soybeans and wheat.
-- -----------------------------------------------------------------------------
CREATE TABLE produce_types (
    produce_type_id     INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    name                VARCHAR(80)     NOT NULL,
    description         VARCHAR(255)    NULL,
    unit_of_measure     VARCHAR(20)     NOT NULL,
    is_active           TINYINT(1)      NOT NULL DEFAULT 1,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (produce_type_id),
    UNIQUE KEY uq_produce_types_name (name),
    CONSTRAINT chk_produce_types_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB COMMENT='Catalogue of agricultural produce types offered at auction';

-- -----------------------------------------------------------------------------
-- 5. QUALITY_GRADES
-- Lookup table for inspection grades.
-- -----------------------------------------------------------------------------
CREATE TABLE quality_grades (
    grade_id        INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    grade_code      VARCHAR(20)     NOT NULL,
    grade_name      VARCHAR(80)     NOT NULL,
    description     VARCHAR(255)    NULL,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (grade_id),
    UNIQUE KEY uq_quality_grades_code (grade_code),
    CONSTRAINT chk_quality_grades_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB COMMENT='Quality grades assigned to inspected produce lots';

-- -----------------------------------------------------------------------------
-- 6. DEPOTS
-- Physical storage and auction locations.
-- -----------------------------------------------------------------------------
CREATE TABLE depots (
    depot_id        INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    depot_code      VARCHAR(20)     NOT NULL,
    depot_name      VARCHAR(120)    NOT NULL,
    location        VARCHAR(150)    NOT NULL,
    capacity        DECIMAL(12,3)   NOT NULL,
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (depot_id),
    UNIQUE KEY uq_depots_code (depot_code),
    CONSTRAINT chk_depots_capacity_positive CHECK (capacity > 0),
    CONSTRAINT chk_depots_is_active CHECK (is_active IN (0, 1))
) ENGINE=InnoDB COMMENT='Depots where produce lots are stored and auctioned';

-- -----------------------------------------------------------------------------
-- 7. PRODUCE_LOTS
-- One inspected consignment of produce belonging to one farmer.
-- -----------------------------------------------------------------------------
CREATE TABLE produce_lots (
    lot_id              INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    lot_number          VARCHAR(30)     NOT NULL,
    farmer_id           INT UNSIGNED    NOT NULL,
    produce_type_id     INT UNSIGNED    NOT NULL,
    grade_id            INT UNSIGNED    NOT NULL,
    depot_id            INT UNSIGNED    NOT NULL,
    quantity            DECIMAL(12,3)   NOT NULL,
    unit_of_measure     VARCHAR(20)     NOT NULL,
    inspection_date     DATE            NOT NULL,
    auction_start       DATETIME        NOT NULL,
    auction_end         DATETIME        NOT NULL,
    minimum_bid_price   DECIMAL(12,2)   NOT NULL,
    status              ENUM(
                            'REGISTERED',
                            'OPEN',
                            'CLOSED',
                            'SOLD',
                            'UNSOLD',
                            'COLLECTED'
                        )               NOT NULL DEFAULT 'REGISTERED',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (lot_id),
    UNIQUE KEY uq_produce_lots_number (lot_number),
    KEY idx_produce_lots_status (status),
    KEY idx_produce_lots_auction_window (auction_start, auction_end),
    CONSTRAINT fk_lots_farmer
        FOREIGN KEY (farmer_id) REFERENCES farmers (farmer_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_lots_produce_type
        FOREIGN KEY (produce_type_id) REFERENCES produce_types (produce_type_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_lots_grade
        FOREIGN KEY (grade_id) REFERENCES quality_grades (grade_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_lots_depot
        FOREIGN KEY (depot_id) REFERENCES depots (depot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT chk_lots_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_lots_min_bid_positive CHECK (minimum_bid_price > 0),
    CONSTRAINT chk_lots_auction_end_after_start CHECK (auction_end > auction_start)
) ENGINE=InnoDB COMMENT='Auction lots of inspected produce stored at a depot';

-- -----------------------------------------------------------------------------
-- 8. BIDS
-- A buyer may place many bids. Only VALID bids compete for the win.
-- -----------------------------------------------------------------------------
CREATE TABLE bids (
    bid_id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    lot_id          INT UNSIGNED    NOT NULL,
    buyer_id        INT UNSIGNED    NOT NULL,
    bid_amount      DECIMAL(12,2)   NOT NULL,
    bid_time        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          ENUM(
                        'VALID',
                        'WITHDRAWN',
                        'WINNING',
                        'REJECTED'
                    )               NOT NULL DEFAULT 'VALID',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bid_id),
    KEY idx_bids_lot_status (lot_id, status),
    KEY idx_bids_buyer (buyer_id),
    CONSTRAINT fk_bids_lot
        FOREIGN KEY (lot_id) REFERENCES produce_lots (lot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_bids_buyer
        FOREIGN KEY (buyer_id) REFERENCES buyers (buyer_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT chk_bids_amount_positive CHECK (bid_amount > 0)
) ENGINE=InnoDB COMMENT='Bids placed by registered buyers on produce lots';

-- -----------------------------------------------------------------------------
-- 9. SUCCESSFUL_SALES
-- lot_id is UNIQUE so the same lot cannot be sold more than once.
-- winning_bid_id is UNIQUE so one bid cannot win two sales.
-- -----------------------------------------------------------------------------
CREATE TABLE successful_sales (
    sale_id             INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    sale_reference      VARCHAR(40)     NOT NULL,
    lot_id              INT UNSIGNED    NOT NULL,
    winning_bid_id      INT UNSIGNED    NOT NULL,
    buyer_id            INT UNSIGNED    NOT NULL,
    sale_amount         DECIMAL(12,2)   NOT NULL,
    sale_date           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status              ENUM(
                            'PAYMENT_PENDING',
                            'PARTIALLY_PAID',
                            'PAID',
                            'COLLECTED',
                            'CANCELLED'
                        )               NOT NULL DEFAULT 'PAYMENT_PENDING',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (sale_id),
    UNIQUE KEY uq_sales_reference (sale_reference),
    UNIQUE KEY uq_sales_lot_id (lot_id),
    UNIQUE KEY uq_sales_winning_bid_id (winning_bid_id),
    KEY idx_sales_buyer (buyer_id),
    KEY idx_sales_status (status),
    CONSTRAINT fk_sales_lot
        FOREIGN KEY (lot_id) REFERENCES produce_lots (lot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_sales_winning_bid
        FOREIGN KEY (winning_bid_id) REFERENCES bids (bid_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_sales_buyer
        FOREIGN KEY (buyer_id) REFERENCES buyers (buyer_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT chk_sales_amount_positive CHECK (sale_amount > 0)
) ENGINE=InnoDB COMMENT='One successful sale per sold lot, created from the winning bid';

-- -----------------------------------------------------------------------------
-- 10. PAYMENTS
-- A sale may have several payments. Overpayment is prevented in later phases.
-- -----------------------------------------------------------------------------
CREATE TABLE payments (
    payment_id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    sale_id             INT UNSIGNED    NOT NULL,
    payment_reference   VARCHAR(40)     NOT NULL,
    amount              DECIMAL(12,2)   NOT NULL,
    payment_method      ENUM(
                            'BANK_TRANSFER',
                            'CASH',
                            'MOBILE_MONEY'
                        )               NOT NULL,
    payment_date        DATETIME        NOT NULL,
    status              ENUM(
                            'PENDING',
                            'VERIFIED',
                            'REJECTED'
                        )               NOT NULL DEFAULT 'PENDING',
    recorded_by         INT UNSIGNED    NOT NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (payment_id),
    UNIQUE KEY uq_payments_reference (payment_reference),
    KEY idx_payments_sale (sale_id),
    KEY idx_payments_status (status),
    CONSTRAINT fk_payments_sale
        FOREIGN KEY (sale_id) REFERENCES successful_sales (sale_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_payments_staff
        FOREIGN KEY (recorded_by) REFERENCES staff (staff_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT chk_payments_amount_positive CHECK (amount > 0)
) ENGINE=InnoDB COMMENT='Payments recorded against successful sales';

-- -----------------------------------------------------------------------------
-- 11. COLLECTIONS
-- sale_id is UNIQUE so a sale normally has one final collection record.
-- -----------------------------------------------------------------------------
CREATE TABLE collections (
    collection_id           INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    sale_id                 INT UNSIGNED    NOT NULL,
    collection_reference    VARCHAR(40)     NOT NULL,
    collected_quantity      DECIMAL(12,3)   NOT NULL,
    collection_date         DATETIME        NOT NULL,
    collected_by            VARCHAR(120)    NOT NULL,
    notes                   VARCHAR(255)    NULL,
    created_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_id),
    UNIQUE KEY uq_collections_sale_id (sale_id),
    UNIQUE KEY uq_collections_reference (collection_reference),
    CONSTRAINT fk_collections_sale
        FOREIGN KEY (sale_id) REFERENCES successful_sales (sale_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT chk_collections_quantity_positive CHECK (collected_quantity > 0)
) ENGINE=InnoDB COMMENT='Final collection of purchased produce against a sale';
