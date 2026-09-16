# Live demonstration script

Demo staff (from `database/seed.sql`). These are **intentional coursework accounts**, not production passwords.

| Username | Password | Role |
|---|---|---|
| `chanda.admin` | `Admin#2026` | ADMIN |
| `mwansa.operator` | `Operator#2026` | OPERATOR |
| `tembo.clerk` | `Clerk#2026` | AUCTION_CLERK |
| `zulu.finance` | `Finance#2026` | FINANCE |
| `banda.viewer` | `Viewer#2026` | VIEWER |

Use `tembo.clerk` / `Clerk#2026` for bidding and close.

---

## 1. Login

Open `/login`. Sign in as `chanda.admin`. Show the sidebar. Log out. Sign in as `banda.viewer` — Farmers is hidden. Paste `/farmers/` anyway: **403 — You do not have permission**.

## 2. Dashboard

Sign in as admin. Cards (farmers, buyers, open auctions, lots sold, totals, outstanding, pending collections) come from `SELECT COUNT/SUM`, not typed figures. Four Chart.js charts use grouped SQL.

## 3. Register farmer

Farmers → Register farmer. Save. Code is `FRM-00xx`.

## 4. Register buyer

Buyers → Register buyer.

## 5. Create produce lot

Lots → Register lot. Active farmer, produce, grade, depot. Quantity and minimum bid > 0. End after start. Status **REGISTERED**.

## 6. Open auction

On the lot page: **Open auction** (ADMIN or AUCTION_CLERK). Status **OPEN**.

## 7. Place bids

Sign in as `tembo.clerk`. Bids → Place bid. Same lot, two different buyers, second amount higher. Bid history on the lot page; highest shown.

## 8. Close auction

Auctions → **Close auction**. Confirm.

Show: winning buyer, winning bid, sale reference, sale amount, status. If you close an OPEN lot with no VALID bids: **Auction closed — no winner**.

Explain `UNIQUE(lot_id)` on `successful_sales` and `sp_close_auction`.

## 9. Record payment

Finance login. Payments → Record payment. Verified amount. Sale status becomes `PARTIALLY_PAID` or `PAID`. Try an overpay: **Payment exceeds the outstanding balance.**

## 10. Collection

Only when status is `PAID`. Collection sets sale and lot to `COLLECTED`.

## 11. Reports

Reports page: farmer supply, buyer purchasing, sales summary, outstanding. Mention `COUNT`, `SUM`, `AVG`, `GROUP BY`.

## 12. Database demonstration (Workbench)

- ERD: `docs/erd.md`
- `SHOW TABLES;` `SHOW CREATE TABLE successful_sales\G` — `uq_sales_lot_id`
- `SHOW FULL TABLES WHERE Table_type = 'VIEW';`
- `SHOW PROCEDURE STATUS WHERE Db = 'agriauction';`
- `SHOW INDEX FROM produce_lots;`
- Run the INNER JOIN and subquery in `database/queries.sql`

## 13. Transaction demonstration

Follow `docs/transactions.md`: successful `CALL sp_close_auction` (COMMIT) then a close on a non-OPEN lot (ROLLBACK / SIGNAL).

## 14. Security

| Kind | Example | Job |
|---|---|---|
| Application user | `chanda.admin` in `staff` | Website login, role |
| MySQL user | `agriauction_app` | Connect and run SQL |

Passwords: bcrypt on `staff`. Flask sessions: `user_id`, `username`, `role` only. CSRF on signed-in POSTs. Least privilege: `docs/security.md`.

## 15. Backup

Show `docs/backup-recovery.md` and a `mysqldump` command with a placeholder password.
