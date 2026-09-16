# AgriAuction Indexing

Indexes speed up `WHERE`, `JOIN` and `ORDER BY` when they match the columns used in a query. They are not free: each `INSERT` and `UPDATE` must also update the index. AgriAuction therefore indexes keys, status filters and the queries that close auctions and record payments — not every column.

MySQL InnoDB already creates an index for:

- every **PRIMARY KEY**
- every **UNIQUE** constraint
- every **FOREIGN KEY** (if no useful index already exists)

Those indexes come from `database/schema.sql`. Extra indexes are in `database/indexes.sql`. MySQL 8.0 does not support `CREATE INDEX IF NOT EXISTS`, so `indexes.sql` is meant to be loaded **once** after the schema.

After loading seed data, run the `EXPLAIN` examples in MySQL Workbench. Look at `key` (which index was chosen) and `rows` (how many rows MySQL expects to read).

---

## 1. Indexes created with the schema

### `PRIMARY KEY` on every table

- **Columns:** the table’s id, for example `produce_lots.lot_id`
- **Query it helps:** `WHERE lot_id = 16`, and all foreign-key parent lookups
- **Why:** the clustered index *is* the table in InnoDB. Point lookups by id are the common case for view, edit and close-auction.

### Unique business codes

| Index | Table | Column(s) | Typical query |
|---|---|---|---|
| `uq_farmers_code` | `farmers` | `farmer_code` | Find farmer `FRM-0001` |
| `uq_buyers_code` | `buyers` | `buyer_code` | Find buyer `BUY-0003` |
| `uq_produce_lots_number` | `produce_lots` | `lot_number` | Search lot `LOT-2026-0016` |
| `uq_sales_reference` | `successful_sales` | `sale_reference` | Look up `SAL-2026-0008` |
| `uq_payments_reference` | `payments` | `payment_reference` | Look up a receipt number |

**Why:** clerks search by the printed code, not by the internal integer id.

### `uq_sales_lot_id` on `successful_sales (lot_id)`

- **Query it helps:** `INSERT INTO successful_sales ...` inside `sp_close_auction`
- **Why:** uniqueness is a correctness rule (one sale per lot), not only a speed trick. The index also makes “has this lot already been sold?” a cheap lookup.

### `idx_produce_lots_status` on `produce_lots (status)`

```sql
EXPLAIN
SELECT lot_number, auction_end
FROM produce_lots
WHERE status = 'OPEN';
```

- **Why:** the dashboard and auction clerk screens filter by status constantly. Status has few distinct values, but the column is used in almost every lot list, so the index is still justified together with more selective composites below.

### `idx_produce_lots_auction_window` on `produce_lots (auction_start, auction_end)`

- **Query it helps:** lots whose auction is in a date range
- **Why:** range filters on the auction window would otherwise scan every lot.

### `idx_farmers_name` on `farmers (last_name, first_name)`

- **Query it helps:** `WHERE last_name LIKE 'Phiri%'` or ordered farmer lists
- **Why:** operators search farmers by name. A left-prefix `LIKE 'Phiri%'` can use this index; `LIKE '%Phiri%'` cannot.

### `idx_buyers_business_name` on `buyers (business_name)`

- **Query it helps:** search `Green Market Ltd`
- **Why:** the same reason as farmer name search.

### `idx_bids_lot_status` on `bids (lot_id, status)`

- **Query it helps:** all `VALID` bids for one lot
- **Why:** closing an auction and showing bid history always start from one `lot_id`.

### `idx_bids_buyer` / `idx_sales_buyer`

- **Query they help:** “what has this buyer bid on / bought?”
- **Why:** these are the foreign-key columns used in buyer profile screens. InnoDB may already index the FK; the named keys make the intent obvious.

### `idx_payments_sale` and `idx_payments_status`

- **Query they help:** payment history for a sale; lists of `PENDING` payments
- **Why:** finance staff work by sale and by payment status.

---

## 2. Extra indexes (`database/indexes.sql`)

### `idx_produce_lots_status_end` on `produce_lots (status, auction_end)`

```sql
EXPLAIN
SELECT lot_id, lot_number, auction_end
FROM produce_lots
WHERE status = 'OPEN'
ORDER BY auction_end;
```

- **Why:** a composite index matches **filter + sort**. `status` alone cannot order by `auction_end` without an extra filesort.

### `idx_produce_lots_farmer_status` on `produce_lots (farmer_id, status)`

```sql
EXPLAIN
SELECT lot_number, status, quantity
FROM produce_lots
WHERE farmer_id = 1
  AND status = 'SOLD';
```

- **Why:** farmer supply reports always start from one farmer, then restrict by lot status.

### `idx_produce_lots_type_status` on `produce_lots (produce_type_id, status)`

```sql
EXPLAIN
SELECT lot_number, quantity
FROM produce_lots
WHERE produce_type_id = 1
  AND status = 'OPEN';
```

- **Why:** “open maize auctions” is a typical clerk filter.

### `idx_bids_winner_selection` on `bids (lot_id, status, bid_amount, bid_time)`

```sql
EXPLAIN
SELECT bid_id, buyer_id, bid_amount, bid_time
FROM bids
WHERE lot_id = 16
  AND status = 'VALID'
ORDER BY bid_amount DESC, bid_time ASC
LIMIT 1;
```

- **Why:** this is the exact access path of `sp_close_auction`. MySQL can find the highest valid bid (and the earliest equal bid) without sorting the whole bid table.

### `idx_payments_sale_status` on `payments (sale_id, status)`

```sql
EXPLAIN
SELECT COALESCE(SUM(amount), 0) AS verified_total
FROM payments
WHERE sale_id = 8
  AND status = 'VERIFIED';
```

- **Why:** `sp_record_payment` and `vw_sales_payment_summary` both sum **verified** payments for **one sale**. The composite index is more selective than `sale_id` or `status` alone.

### `idx_sales_date` on `successful_sales (sale_date)`

```sql
EXPLAIN
SELECT sale_reference, sale_amount
FROM successful_sales
WHERE sale_date >= '2026-06-01'
  AND sale_date < '2026-07-01';
```

- **Why:** monthly sales reports are range scans on `sale_date`.

### `idx_payments_date` on `payments (payment_date)`

```sql
EXPLAIN
SELECT payment_reference, amount, status
FROM payments
WHERE payment_date >= '2026-08-01'
  AND payment_date < '2026-09-01';
```

- **Why:** finance period reports filter payments by date.

---

## 3. Indexes we did **not** add

| Column | Reason |
|---|---|
| `farmers.email` | Optional, rarely used as a search key |
| `produce_lots.quantity` | Range filters on quantity are uncommon |
| `bids.bid_amount` alone | Amount is always used **with** `lot_id` |
| `staff.role` | Very few staff rows; a full scan is cheap |
| Leading-wildcard name search | `LIKE '%Phiri%'` cannot use a B-tree index anyway |

---

## 4. How to read EXPLAIN (viva notes)

| Column | Meaning |
|---|---|
| `type` | `const` / `ref` / `range` are better than `ALL` (full table scan) |
| `possible_keys` | Indexes MySQL considered |
| `key` | Index actually used |
| `rows` | Estimated rows to read |
| `Extra` | `Using filesort` or `Using temporary` often means the index does not match `ORDER BY` / `GROUP BY` |

The goal is not “every query uses an index”. The goal is that the **hot paths** — open lots, winner selection, payment totals — do not scan the whole table as data grows.
