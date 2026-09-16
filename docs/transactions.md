# Transactions and ACID in AgriAuction

The most important transaction is **closing an auction**. It lives in `sp_close_auction` (`database/procedures.sql`). Flask calls it with `callproc("sp_close_auction", (lot_id,))` so the web app does not assemble the sale by hand.

Application users (`staff`) are not MySQL users. The connection is `agriauction_app`. The procedure still runs inside that connection, with InnoDB row locks.

---

## The auction-close transaction

```text
START TRANSACTION
SELECT lot ... FOR UPDATE          -- lock the lot
check status is OPEN
SELECT COUNT(*) FROM bids ... FOR UPDATE
find highest VALID bid (amount DESC, time ASC)
IF winner:
    mark bid WINNING
    INSERT successful_sales        -- UNIQUE(lot_id) blocks a second sale
    mark lot SOLD
ELSE:
    mark lot UNSOLD
COMMIT
```

On any SQL error the `EXIT HANDLER` runs `ROLLBACK` and re-raises the error. The lot cannot be `SOLD` without a matching sale row, because both changes are in the same transaction.

---

## ACID (viva)

### Atomicity

All close-auction changes succeed, or none do. You never keep a `WINNING` bid without a sale, or a `SOLD` lot without `successful_sales`.

### Consistency

Foreign keys (`lot_id`, `buyer_id`, `winning_bid_id`) and CHECKs (`sale_amount > 0`) stay valid. `UNIQUE (lot_id)` on `successful_sales` is the last guard against two sales for one lot.

### Isolation

`SELECT ... FOR UPDATE` locks the lot (and its bids) so two clerks cannot close the same OPEN lot at the same time. The second session waits, then sees the lot is no longer OPEN and receives `Only an OPEN lot can be closed.`

### Durability

After `COMMIT`, InnoDB has written the sale (or the UNSOLD status). A server restart does not undo it.

---

## COMMIT demonstration (Workbench)

Use a copy of an OPEN seed lot, or create a throwaway OPEN lot with a VALID bid, then:

```sql
START TRANSACTION;

UPDATE produce_lots
SET status = 'OPEN'
WHERE lot_id = 16
  AND status = 'OPEN';  -- no real change; shows UPDATE inside a transaction

-- Prefer the real procedure instead of manual INSERT:
CALL sp_close_auction(16);

-- The procedure COMMITs internally. After a successful close:
SELECT lot_id, status FROM produce_lots WHERE lot_id = 16;
SELECT sale_reference, lot_id FROM successful_sales WHERE lot_id = 16;
```

Expected: lot `SOLD` and exactly one sale row.

---

## ROLLBACK demonstration

This shows a failed close leaving no half-written sale. Run as a user who can execute the procedure:

```sql
START TRANSACTION;

-- Force a failure: close a lot that is already SOLD.
-- sp_close_auction SIGNALs and ROLLBACKs.
CALL sp_close_auction(1);  -- seed lot 1 is not OPEN

-- Nothing from this attempt is kept.
SELECT COUNT(*) AS sales_for_lot_1
FROM successful_sales
WHERE lot_id = 1;
```

Manual ROLLBACK sketch (do **not** leave this committed on the demo database):

```sql
START TRANSACTION;

UPDATE produce_lots SET status = 'CLOSED' WHERE lot_id = 16;
INSERT INTO successful_sales (
    sale_reference, lot_id, winning_bid_id, buyer_id, sale_amount, status
) VALUES ('SAL-ROLLBACK-DEMO', 16, 1, 1, 100.00, 'PAYMENT_PENDING');

ROLLBACK;

SELECT status FROM produce_lots WHERE lot_id = 16;
SELECT * FROM successful_sales WHERE sale_reference = 'SAL-ROLLBACK-DEMO';
```

After `ROLLBACK` the UPDATE and INSERT are gone.

---

## Other multi-row transactions

| Action | Where | What changes together |
|---|---|---|
| Place bid | `app/routes/bids.py` | Lock OPEN lot, then `INSERT` bid |
| Record payment | `sp_record_payment` | Insert payment, recount verified totals, update sale status |
| Collect produce | `app/routes/collections.py` | Insert collection, sale `COLLECTED`, lot `COLLECTED` |

Payments that would exceed `sale_amount` `SIGNAL` and roll back, so the UI can show: **Payment exceeds the outstanding balance.**
