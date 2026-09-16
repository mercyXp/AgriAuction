# IT212 final requirements audit

Statuses: **DONE** = implemented in this repo and covered by automated tests or SQL files. **PARTIAL** = implemented locally but not proven on live Railway / live MySQL from this workspace. **MISSING** = not present.

| Requirement | Status | Evidence |
|---|---|---|
| Requirements analysis / business rules | DONE | Public `/project` page; schema comments; route validation |
| ERD | DONE | `docs/erd.md` |
| Primary keys | DONE | `database/schema.sql` |
| Foreign keys | DONE | `schema.sql` `ON DELETE RESTRICT` |
| Cardinalities | DONE | `docs/erd.md` |
| Relational schema | DONE | 11 tables in `schema.sql` |
| 1NF / 2NF / 3NF | DONE | `docs/normalization.md` |
| DDL | DONE | `schema.sql`, `indexes.sql`, `views.sql`, `procedures.sql` |
| DML | DONE | `seed.sql`; Flask INSERT/UPDATE; `queries.sql` |
| SELECT / filtering / sorting | DONE | Lists + `queries.sql` |
| Aggregates | DONE | Reports + dashboard + `queries.sql` |
| GROUP BY | DONE | Reports and dashboard charts |
| INNER JOIN | DONE | Lot/sale views and reports |
| Another JOIN (LEFT JOIN) | DONE | `vw_auction_lot_summary`; buyer report; `queries.sql` |
| Subquery | DONE | Buyers above average spend in `queries.sql` |
| Two views | DONE | `vw_auction_lot_summary`, `vw_sales_payment_summary` |
| Two stored procedures | DONE | `sp_close_auction`, `sp_record_payment` |
| Transaction | DONE | Procedures + bid insert + collection |
| ACID notes | DONE | `docs/transactions.md` |
| Indexes | DONE | `database/indexes.sql`, `docs/indexing.md` |
| Security / DB users / authorization | DONE | bcrypt, sessions, CSRF, `security.sql`, `@role_required` |
| Backup / recovery | DONE | `docs/backup-recovery.md` |
| Working web application | PARTIAL | Flask app complete; live MySQL `agriauction_app` was not connected from this environment (1045 until `security.sql` matches `.env`) |
| CRUD | DONE | Farmers, buyers, produce, grades, depots, lots |
| Validation | DONE | Server-side on every write; CHECKs in MySQL |
| Search / filtering | DONE | List screens |
| Reports | DONE | `/reports/` four SQL reports |
| Multi-record transaction | DONE | Auction close, payment, collection |
| Error handling | DONE | 400/403/404/500 + flashed business messages |
| Railway deployment | PARTIAL | `Procfile`, Gunicorn, env mapping in `docs/railway.md`. Deploy and production smoke test were not run from this workspace |

## Deliberately not claimed as live-tested here

- `SOURCE` of schema/seed/security against the student’s MySQL (root password not used)
- Railway service create / domain / plugin attach

Those are operator steps on the student’s machine and Railway account.
