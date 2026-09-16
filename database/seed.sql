-- AgriAuction Digital Produce Trading Platform
-- Phase 4: sample data
--
-- Load AFTER database/schema.sql:
--   Get-Content .\database\seed.sql -Raw | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
--
-- Currency is ZMW. Names, phones and emails are fictional demo data.
--
-- Demo staff passwords (bcrypt hashed below):
--   chanda.admin      Admin#2026
--   mwansa.operator   Operator#2026
--   tembo.clerk       Clerk#2026
--   zulu.finance      Finance#2026
--   banda.viewer      Viewer#2026
--   kabwe.archive     Operator#2026   (inactive)

USE agriauction;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE collections;
TRUNCATE TABLE payments;
TRUNCATE TABLE successful_sales;
TRUNCATE TABLE bids;
TRUNCATE TABLE produce_lots;
TRUNCATE TABLE depots;
TRUNCATE TABLE quality_grades;
TRUNCATE TABLE produce_types;
TRUNCATE TABLE buyers;
TRUNCATE TABLE farmers;
TRUNCATE TABLE staff;
SET FOREIGN_KEY_CHECKS = 1;

-- -----------------------------------------------------------------------------
-- STAFF (6)
-- -----------------------------------------------------------------------------
INSERT INTO staff (
    staff_id, username, email, password_hash, first_name, last_name, role, is_active
) VALUES
(1, 'chanda.admin', 'chanda.admin@agriauction-demo.zm',
    '$2b$12$cOM81MBdfIGUavVN.j/Jdu21o3fFoMpN5/T.d7NwXM8NKtaczzWXi',
    'Chanda', 'Mulenga', 'ADMIN', 1),
(2, 'mwansa.operator', 'mwansa.operator@agriauction-demo.zm',
    '$2b$12$tbGi9Jctg2s5uz4eii/XVOwjs/fWwRi8VlLCFKO9rGwQGARNqyrHm',
    'Mwansa', 'Bwalya', 'OPERATOR', 1),
(3, 'tembo.clerk', 'tembo.clerk@agriauction-demo.zm',
    '$2b$12$RQsYgh5RW4QvbxuUJ/1YW.C6X8HB37flu3gb1vmyUg8bFH79LBcgO',
    'Natasha', 'Tembo', 'AUCTION_CLERK', 1),
(4, 'zulu.finance', 'zulu.finance@agriauction-demo.zm',
    '$2b$12$MUkzw8BMQpfD0l9PJj1iMOrc/UZelsHovcbr8Eh3I7uKP2XINF7AG',
    'Patrick', 'Zulu', 'FINANCE', 1),
(5, 'banda.viewer', 'banda.viewer@agriauction-demo.zm',
    '$2b$12$xbHOxD.xN9aIMZCV5OM04uuATloAa6Y9PqdNxXLAkrchbY6WQMuCG',
    'Loveness', 'Banda', 'VIEWER', 1),
(6, 'kabwe.archive', 'kabwe.archive@agriauction-demo.zm',
    '$2b$12$tbGi9Jctg2s5uz4eii/XVOwjs/fWwRi8VlLCFKO9rGwQGARNqyrHm',
    'Joseph', 'Kabwe', 'OPERATOR', 0);

-- -----------------------------------------------------------------------------
-- FARMERS (12) — fictional Zambian producers
-- -----------------------------------------------------------------------------
INSERT INTO farmers (
    farmer_id, farmer_code, first_name, last_name, phone, email, address,
    farm_name, registration_date, is_active
) VALUES
(1,  'FRM-0001', 'Joseph',  'Mutale',  '0977110001', 'j.mutale@farms-demo.zm',   'Plot 12, Chongwe Road, Lusaka',           'Green Valley Farm',       '2024-01-15', 1),
(2,  'FRM-0002', 'Mary',    'Phiri',   '0977110002', 'm.phiri@farms-demo.zm',    'Farm Block A, Chipata',                   'Eastern Sunrise Farm',    '2024-02-03', 1),
(3,  'FRM-0003', 'Peter',   'Tembo',   '0977110003', 'p.tembo@farms-demo.zm',    'Kalomo Road, Choma',                      'Southern Grain Fields',   '2024-02-20', 1),
(4,  'FRM-0004', 'Grace',   'Zulu',    '0977110004', 'g.zulu@farms-demo.zm',     'Masala Area, Ndola',                      'Copperbelt Groundnut Co', '2024-03-11', 1),
(5,  'FRM-0005', 'Daniel',  'Banda',   '0977110005', 'd.banda@farms-demo.zm',    'Dambwa, Livingstone',                     'Victoria Oilseeds Farm',  '2024-03-28', 1),
(6,  'FRM-0006', 'Esther',  'Mwansa',  '0977110006', 'e.mwansa@farms-demo.zm',   'Great North Road, Kabwe',                 'Central Plateau Farm',    '2024-04-09', 1),
(7,  'FRM-0007', 'Moses',   'Ngoma',   '0977110007', 'm.ngoma@farms-demo.zm',    'Katete District, Eastern Province',       'Katete Family Farm',      '2024-05-02', 1),
(8,  'FRM-0008', 'Ruth',    'Chanda',  '0977110008', 'r.chanda@farms-demo.zm',   'Mazabuka Sugar Belt, Mazabuka',           'Kafue Flats Produce',     '2024-05-21', 1),
(9,  'FRM-0009', 'Isaac',   'Sinkala', '0977110009', 'i.sinkala@farms-demo.zm',  'Mumbwa Road, Lusaka West',                'Westland Maize Farm',     '2024-06-14', 1),
(10, 'FRM-0010', 'Beatrice','Mulenga', '0977110010', 'b.mulenga@farms-demo.zm',  'Mpongwe Block, Copperbelt',               'Mpongwe Nuts & Grain',    '2024-07-01', 1),
(11, 'FRM-0011', 'Samuel',  'Daka',    '0977110011', 's.daka@farms-demo.zm',     'Monze District, Southern Province',       'Monze Sunflower Fields',  '2024-07-18', 1),
(12, 'FRM-0012', 'Naomi',   'Bwalya',  '0977110012', NULL,                      'Petauke District, Eastern Province',      'Petauke Smallholder Farm','2024-08-05', 1);

-- -----------------------------------------------------------------------------
-- BUYERS (12) — fictional trading businesses
-- -----------------------------------------------------------------------------
INSERT INTO buyers (
    buyer_id, buyer_code, business_name, contact_person, phone, email, address,
    registration_date, is_active
) VALUES
(1,  'BUY-0001', 'Lusaka Grain Traders Ltd',      'James Banda',     '0966110001', 'james@lgt-demo.zm',      'Lumumba Road, Lusaka',              '2024-01-20', 1),
(2,  'BUY-0002', 'Copperbelt Millers',            'Alice Phiri',     '0966110002', 'alice@cbm-demo.zm',      'President Avenue, Ndola',           '2024-02-08', 1),
(3,  'BUY-0003', 'Green Market Ltd',              'Chanda Mwila',    '0966110003', 'chanda@gml-demo.zm',     'Soweto Market, Lusaka',             '2024-02-22', 1),
(4,  'BUY-0004', 'Eastern Produce Buyers',        'Moses Zimba',     '0966110004', 'moses@epb-demo.zm',      'Umodzi Highway, Chipata',           '2024-03-05', 1),
(5,  'BUY-0005', 'Kafue Feed Industries',         'Thandiwe Zulu',   '0966110005', 'thandiwe@kfi-demo.zm',   'Kafue Town, Lusaka Province',        '2024-03-19', 1),
(6,  'BUY-0006', 'Southern Mills Co',             'Peter Mwanza',    '0966110006', 'peter@smc-demo.zm',      'Livingstone Road, Choma',           '2024-04-02', 1),
(7,  'BUY-0007', 'ZamOil Crushers',               'Grace Tembo',     '0966110007', 'grace@zamoil-demo.zm',   'Industrial Area, Lusaka',           '2024-04-16', 1),
(8,  'BUY-0008', 'Ndola Commodity Exchange Desk', 'Brian Mwale',     '0966110008', 'brian@nced-demo.zm',     'Broadway, Ndola',                   '2024-05-07', 1),
(9,  'BUY-0009', 'Victoria Falls Foods',          'Lillian Sakala',  '0966110009', 'lillian@vff-demo.zm',    'Mosi-oa-Tunya Road, Livingstone',   '2024-05-25', 1),
(10, 'BUY-0010', 'Mazabuka Agri Supplies',        'Henry Chisanga',  '0966110010', 'henry@mas-demo.zm',      'Town Centre, Mazabuka',             '2024-06-10', 1),
(11, 'BUY-0011', 'Kitwe Wholesale Grains',        'Faith Musonda',   '0966110011', 'faith@kwg-demo.zm',      'Independence Avenue, Kitwe',        '2024-07-04', 1),
(12, 'BUY-0012', 'Northern Traders Ltd',          'Owen Chanda',     '0966110012', 'owen@ntl-demo.zm',       'Kasama Road, Kasama',               '2024-08-12', 0);

-- -----------------------------------------------------------------------------
-- PRODUCE TYPES (5)
-- -----------------------------------------------------------------------------
INSERT INTO produce_types (produce_type_id, name, description, unit_of_measure, is_active) VALUES
(1, 'Maize',      'White and yellow maize for milling and feed',           'tonne', 1),
(2, 'Soybeans',   'Soybeans for crushing and protein meal',                'tonne', 1),
(3, 'Wheat',      'Bread wheat delivered to commercial millers',           'tonne', 1),
(4, 'Groundnuts', 'Shelled and unshelled groundnuts',                      'tonne', 1),
(5, 'Sunflower',  'Sunflower seed for edible oil',                         'tonne', 1);

-- -----------------------------------------------------------------------------
-- QUALITY GRADES (3)
-- -----------------------------------------------------------------------------
INSERT INTO quality_grades (grade_id, grade_code, grade_name, description, is_active) VALUES
(1, 'A', 'Grade A', 'Highest quality, low moisture, few foreign materials', 1),
(2, 'B', 'Grade B', 'Good commercial quality, acceptable moisture',         1),
(3, 'C', 'Grade C', 'Lower commercial grade, still fit for trade',          1);

-- -----------------------------------------------------------------------------
-- DEPOTS (5) — Zambian locations
-- -----------------------------------------------------------------------------
INSERT INTO depots (depot_id, depot_code, depot_name, location, capacity, is_active) VALUES
(1, 'LSK-01', 'Lusaka National Auction Yard', 'Lusaka',      8000.000, 1),
(2, 'CHT-01', 'Chipata Produce Depot',        'Chipata',     3500.000, 1),
(3, 'CHO-01', 'Choma Grain Centre',           'Choma',       4000.000, 1),
(4, 'NDL-01', 'Ndola Produce Hub',            'Ndola',       5000.000, 1),
(5, 'LIV-01', 'Livingstone Auction Depot',    'Livingstone', 2500.000, 1);

-- -----------------------------------------------------------------------------
-- PRODUCE LOTS (18)
-- Status mix: COLLECTED, SOLD, UNSOLD, REGISTERED, OPEN
-- -----------------------------------------------------------------------------
INSERT INTO produce_lots (
    lot_id, lot_number, farmer_id, produce_type_id, grade_id, depot_id,
    quantity, unit_of_measure, inspection_date, auction_start, auction_end,
    minimum_bid_price, status
) VALUES
-- Collected (lots 1-5)
(1,  'LOT-2026-0001', 1, 1, 1, 1, 25.000, 'tonne', '2026-05-28', '2026-06-01 08:00:00', '2026-06-05 17:00:00', 4200.00, 'COLLECTED'),
(2,  'LOT-2026-0002', 2, 2, 1, 2, 18.500, 'tonne', '2026-06-02', '2026-06-06 08:00:00', '2026-06-10 17:00:00', 6100.00, 'COLLECTED'),
(3,  'LOT-2026-0003', 3, 3, 2, 3, 12.000, 'tonne', '2026-06-08', '2026-06-12 08:00:00', '2026-06-16 17:00:00', 5000.00, 'COLLECTED'),
(4,  'LOT-2026-0004', 4, 4, 1, 4,  8.250, 'tonne', '2026-06-14', '2026-06-18 08:00:00', '2026-06-22 17:00:00', 7200.00, 'COLLECTED'),
(5,  'LOT-2026-0005', 5, 5, 2, 5, 10.000, 'tonne', '2026-06-20', '2026-06-24 08:00:00', '2026-06-28 17:00:00', 5500.00, 'COLLECTED'),
-- Sold and fully paid, not yet collected
(6,  'LOT-2026-0006', 6, 1, 2, 1, 30.000, 'tonne', '2026-07-02', '2026-07-06 08:00:00', '2026-07-10 17:00:00', 4000.00, 'SOLD'),
(7,  'LOT-2026-0007', 7, 2, 1, 2, 22.000, 'tonne', '2026-07-08', '2026-07-12 08:00:00', '2026-07-16 17:00:00', 6000.00, 'SOLD'),
-- Sold, partially paid
(8,  'LOT-2026-0008', 8, 3, 1, 3, 15.000, 'tonne', '2026-08-01', '2026-08-04 08:00:00', '2026-08-08 17:00:00', 5100.00, 'SOLD'),
(9,  'LOT-2026-0009', 9, 1, 3, 1, 40.000, 'tonne', '2026-08-06', '2026-08-10 08:00:00', '2026-08-14 17:00:00', 3800.00, 'SOLD'),
-- Sold, payment still pending
(10, 'LOT-2026-0010', 10, 4, 2, 4, 6.000, 'tonne', '2026-08-12', '2026-08-16 08:00:00', '2026-08-20 17:00:00', 7000.00, 'SOLD'),
(11, 'LOT-2026-0011', 11, 5, 1, 5, 9.500, 'tonne', '2026-08-18', '2026-08-22 08:00:00', '2026-08-26 17:00:00', 5600.00, 'SOLD'),
-- Closed with no winner
(12, 'LOT-2026-0012', 12, 1, 3, 2, 5.000, 'tonne', '2026-08-20', '2026-08-24 08:00:00', '2026-08-28 17:00:00', 3900.00, 'UNSOLD'),
(13, 'LOT-2026-0013', 1,  3, 3, 3, 7.000, 'tonne', '2026-08-22', '2026-08-26 08:00:00', '2026-08-30 17:00:00', 4800.00, 'UNSOLD'),
-- Registered, auction not opened yet
(14, 'LOT-2026-0014', 2, 2, 2, 1, 11.000, 'tonne', '2026-09-10', '2026-10-01 08:00:00', '2026-10-05 17:00:00', 6000.00, 'REGISTERED'),
(15, 'LOT-2026-0015', 3, 4, 3, 4,  4.500, 'tonne', '2026-09-12', '2026-10-02 08:00:00', '2026-10-06 17:00:00', 6800.00, 'REGISTERED'),
-- Currently open (as at 16 Sep 2026)
(16, 'LOT-2026-0016', 4, 1, 1, 1, 20.000, 'tonne', '2026-09-08', '2026-09-12 08:00:00', '2026-10-20 17:00:00', 4300.00, 'OPEN'),
(17, 'LOT-2026-0017', 5, 5, 1, 3, 14.000, 'tonne', '2026-09-09', '2026-09-13 08:00:00', '2026-10-18 17:00:00', 5400.00, 'OPEN'),
(18, 'LOT-2026-0018', 6, 2, 2, 4, 16.750, 'tonne', '2026-09-11', '2026-09-14 08:00:00', '2026-10-25 17:00:00', 6050.00, 'OPEN');

-- -----------------------------------------------------------------------------
-- BIDS (37)
-- Lot 5 has a tie: two bids of ZMW 6000.00; the earlier bid wins.
-- -----------------------------------------------------------------------------
INSERT INTO bids (bid_id, lot_id, buyer_id, bid_amount, bid_time, status) VALUES
-- Lot 1
(1,  1, 1,  4500.00, '2026-06-02 09:10:00', 'VALID'),
(2,  1, 2,  4700.00, '2026-06-03 11:20:00', 'VALID'),
(3,  1, 3,  4800.00, '2026-06-04 14:05:00', 'WINNING'),
-- Lot 2
(4,  2, 4,  6200.00, '2026-06-07 10:00:00', 'VALID'),
(5,  2, 5,  6500.00, '2026-06-09 16:40:00', 'WINNING'),
(6,  2, 1,  6400.00, '2026-06-09 12:15:00', 'VALID'),
-- Lot 3
(7,  3, 6,  5200.00, '2026-06-13 09:30:00', 'VALID'),
(8,  3, 7,  5400.00, '2026-06-15 15:10:00', 'WINNING'),
-- Lot 4
(9,  4, 8,  7500.00, '2026-06-19 08:45:00', 'VALID'),
(10, 4, 9,  8000.00, '2026-06-21 13:25:00', 'WINNING'),
(11, 4, 2,  7800.00, '2026-06-21 11:00:00', 'VALID'),
-- Lot 5 — tie at 6000; bid 12 is earlier so it wins
(12, 5, 3,  6000.00, '2026-06-25 08:00:00', 'WINNING'),
(13, 5, 4,  6000.00, '2026-06-25 09:00:00', 'VALID'),
(14, 5, 5,  5800.00, '2026-06-26 10:20:00', 'VALID'),
-- Lot 6
(15, 6, 6,  4200.00, '2026-07-07 09:00:00', 'VALID'),
(16, 6, 7,  4450.00, '2026-07-09 16:30:00', 'WINNING'),
-- Lot 7
(17, 7, 8,  6150.00, '2026-07-13 10:10:00', 'VALID'),
(18, 7, 9,  6300.00, '2026-07-15 14:50:00', 'WINNING'),
(19, 7, 10, 6200.00, '2026-07-14 11:00:00', 'WITHDRAWN'),
-- Lot 8
(20, 8, 1,  5400.00, '2026-08-05 09:40:00', 'VALID'),
(21, 8, 11, 5600.00, '2026-08-07 15:15:00', 'WINNING'),
-- Lot 9
(22, 9, 2,  4000.00, '2026-08-11 08:20:00', 'VALID'),
(23, 9, 3,  4100.00, '2026-08-13 12:00:00', 'WINNING'),
-- Lot 10
(24, 10, 4, 7200.00, '2026-08-17 09:05:00', 'VALID'),
(25, 10, 5, 7400.00, '2026-08-19 16:00:00', 'WINNING'),
-- Lot 11
(26, 11, 6, 5700.00, '2026-08-23 10:30:00', 'VALID'),
(27, 11, 7, 5900.00, '2026-08-25 13:45:00', 'WINNING'),
-- Lot 12 unsold: no valid competing bid
(28, 12, 8, 3500.00, '2026-08-25 09:00:00', 'REJECTED'),
(29, 12, 9, 4000.00, '2026-08-26 11:30:00', 'WITHDRAWN'),
-- Lot 16 open
(30, 16, 1,  4300.00, '2026-09-13 09:00:00', 'VALID'),
(31, 16, 2,  4450.00, '2026-09-14 11:20:00', 'VALID'),
(32, 16, 10, 4600.00, '2026-09-15 15:40:00', 'VALID'),
-- Lot 17 open
(33, 17, 3,  5400.00, '2026-09-14 08:50:00', 'VALID'),
(34, 17, 4,  5550.00, '2026-09-15 10:05:00', 'VALID'),
-- Lot 18 open
(35, 18, 5,  6100.00, '2026-09-15 09:15:00', 'VALID'),
(36, 18, 11, 6200.00, '2026-09-16 08:00:00', 'VALID'),
(37, 18, 8,  6050.00, '2026-09-15 16:30:00', 'VALID');

-- -----------------------------------------------------------------------------
-- SUCCESSFUL SALES (11)
-- buyer_id matches the winning bid's buyer.
-- -----------------------------------------------------------------------------
INSERT INTO successful_sales (
    sale_id, sale_reference, lot_id, winning_bid_id, buyer_id, sale_amount, sale_date, status
) VALUES
(1,  'SAL-2026-0001', 1,  3,  3,  4800.00, '2026-06-05 17:05:00', 'COLLECTED'),
(2,  'SAL-2026-0002', 2,  5,  5,  6500.00, '2026-06-10 17:05:00', 'COLLECTED'),
(3,  'SAL-2026-0003', 3,  8,  7,  5400.00, '2026-06-16 17:05:00', 'COLLECTED'),
(4,  'SAL-2026-0004', 4,  10, 9,  8000.00, '2026-06-22 17:05:00', 'COLLECTED'),
(5,  'SAL-2026-0005', 5,  12, 3,  6000.00, '2026-06-28 17:05:00', 'COLLECTED'),
(6,  'SAL-2026-0006', 6,  16, 7,  4450.00, '2026-07-10 17:05:00', 'PAID'),
(7,  'SAL-2026-0007', 7,  18, 9,  6300.00, '2026-07-16 17:05:00', 'PAID'),
(8,  'SAL-2026-0008', 8,  21, 11, 5600.00, '2026-08-08 17:05:00', 'PARTIALLY_PAID'),
(9,  'SAL-2026-0009', 9,  23, 3,  4100.00, '2026-08-14 17:05:00', 'PARTIALLY_PAID'),
(10, 'SAL-2026-0010', 10, 25, 5,  7400.00, '2026-08-20 17:05:00', 'PAYMENT_PENDING'),
(11, 'SAL-2026-0011', 11, 27, 7,  5900.00, '2026-08-26 17:05:00', 'PAYMENT_PENDING');

-- -----------------------------------------------------------------------------
-- PAYMENTS (14)
-- Verified totals never exceed the sale amount.
-- -----------------------------------------------------------------------------
INSERT INTO payments (
    payment_id, sale_id, payment_reference, amount, payment_method, payment_date, status, recorded_by
) VALUES
(1,  1,  'PAY-2026-0001', 4800.00, 'BANK_TRANSFER', '2026-06-08 10:00:00', 'VERIFIED', 4),
(2,  2,  'PAY-2026-0002', 6500.00, 'MOBILE_MONEY',  '2026-06-12 09:30:00', 'VERIFIED', 4),
(3,  3,  'PAY-2026-0003', 2700.00, 'CASH',          '2026-06-18 11:00:00', 'VERIFIED', 4),
(4,  3,  'PAY-2026-0004', 2700.00, 'BANK_TRANSFER', '2026-06-20 14:15:00', 'VERIFIED', 4),
(5,  4,  'PAY-2026-0005', 8000.00, 'BANK_TRANSFER', '2026-06-25 08:40:00', 'VERIFIED', 4),
(6,  5,  'PAY-2026-0006', 6000.00, 'CASH',          '2026-07-01 10:20:00', 'VERIFIED', 4),
(7,  6,  'PAY-2026-0007', 4450.00, 'MOBILE_MONEY',  '2026-07-14 16:00:00', 'VERIFIED', 4),
(8,  7,  'PAY-2026-0008', 6300.00, 'BANK_TRANSFER', '2026-07-20 09:10:00', 'VERIFIED', 4),
(9,  8,  'PAY-2026-0009', 2000.00, 'MOBILE_MONEY',  '2026-08-12 12:00:00', 'VERIFIED', 4),
(10, 8,  'PAY-2026-0010', 1500.00, 'BANK_TRANSFER', '2026-08-15 09:45:00', 'PENDING',  4),
(11, 9,  'PAY-2026-0011', 2000.00, 'CASH',          '2026-08-18 11:30:00', 'VERIFIED', 4),
(12, 10, 'PAY-2026-0012', 7400.00, 'BANK_TRANSFER', '2026-08-22 10:00:00', 'REJECTED', 4),
(13, 11, 'PAY-2026-0013', 1000.00, 'MOBILE_MONEY',  '2026-08-28 13:20:00', 'PENDING',  3),
(14, 4,  'PAY-2026-0014',  500.00, 'CASH',          '2026-06-24 15:00:00', 'REJECTED', 4);

-- -----------------------------------------------------------------------------
-- COLLECTIONS (5) — only fully paid collected sales
-- -----------------------------------------------------------------------------
INSERT INTO collections (
    collection_id, sale_id, collection_reference, collected_quantity,
    collection_date, collected_by, notes
) VALUES
(1, 1, 'COL-2026-0001', 25.000, '2026-06-12 09:00:00', 'Chanda Mwila',    'Collected in full from Lusaka yard'),
(2, 2, 'COL-2026-0002', 18.500, '2026-06-16 10:30:00', 'Thandiwe Zulu',   'Loaded onto Kafue Feed trucks'),
(3, 3, 'COL-2026-0003', 12.000, '2026-06-24 08:45:00', 'Grace Tembo',     'Wheat collected for crushing'),
(4, 4, 'COL-2026-0004',  8.250, '2026-06-29 14:00:00', 'Lillian Sakala',  'Groundnuts sealed and weighed'),
(5, 5, 'COL-2026-0005', 10.000, '2026-07-04 11:15:00', 'Chanda Mwila',    'Sunflower seed collected after cash payment');
