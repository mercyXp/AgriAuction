# AgriAuction Database Users and Security

AgriAuction has two different kinds of “user”. Mixing them up is a common viva mistake.

| Kind | Stored in | Example | Purpose |
|---|---|---|---|
| **Application users** | table `staff` | `chanda.admin` | Log into the **website**. Roles such as ADMIN or FINANCE. |
| **MySQL users** | MySQL itself (`mysql.user`) | `agriauction_app` | Connect to the **database**. Privileges such as SELECT or INSERT. |

A clerk who logs in as `mwansa.operator` is **not** a MySQL account. Flask connects once, as `agriauction_app`, then looks up the clerk in `staff`.

Passwords for MySQL users are **not** in Git. They are set in your session when you load `database/security.sql`, and the app password is copied into gitignored `.env`.

---

## 1. Application users (`staff`)

Created in Phase 2 (`schema.sql`) and seeded in Phase 4.

- Login name, email, **bcrypt** `password_hash`, name, `role`, `is_active`
- Roles: `ADMIN`, `OPERATOR`, `AUCTION_CLERK`, `FINANCE`, `VIEWER`
- Used later for Flask sessions and page-level authorization
- Cannot connect to MySQL Workbench with a staff username

`staff.role` is **application** authorization. It does not appear in `SHOW GRANTS`.

---

## 2. MySQL users

Created by `database/security.sql`. Each account exists twice (`@'localhost'` and `@'127.0.0.1'`) because Windows Flask often uses TCP (`127.0.0.1`), while Workbench may use `localhost`.

MySQL 8 default authentication is `caching_sha2_password`. `mysql-connector-python` 9.x supports that.

### `agriauction_app` — what Flask will use (Phase 7+)

**Privileges:** `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `EXECUTE`, `SHOW VIEW` on `agriauction.*`

| Allowed | Not allowed |
|---|---|
| Read and write table rows | `CREATE` / `ALTER` / `DROP` tables |
| `CALL sp_close_auction` / `sp_record_payment` | Create users or grant privileges |
| `SELECT` from views | `SHUTDOWN`, `FILE`, other servers’ databases |

This is **least privilege** for the web app: enough to run the system, not enough to destroy the schema if a query is wrong or injected.

`.env` (gitignored) should match:

```text
DB_USER=agriauction_app
DB_PASSWORD=<the @app_password you set>
DB_NAME=agriauction
```

Do **not** set `DB_USER=root` for the Flask app.

### `agriauction_reporting` — read-only

**Privileges:** `SELECT`, `SHOW VIEW` on `agriauction.*`

Use this in Workbench for reports, `EXPLAIN`, and viva demonstrations that should not change data. `INSERT` / `UPDATE` / `DELETE` / `CALL` should fail with error 1142 (command denied).

### `agriauction_admin` — schema administration

**Privileges:** `ALL PRIVILEGES` on `agriauction.*` `WITH GRANT OPTION`

Use this in Workbench to change tables, views, procedures, and indexes **on this database only**. It is still not MySQL `root`:

- no `CREATE USER` (that is a global privilege)
- no access to other databases
- no server shutdown

Creating the three accounts the first time is a **root** job. Day-to-day admin of `agriauction` can use `agriauction_admin`.

---

## 3. Least privilege (viva)

Grant the smallest set of rights that still lets the account do its job.

```sql
-- Too much (do not use for Flask)
GRANT ALL PRIVILEGES ON *.* TO 'agriauction_app'@'localhost';

-- Right size for Flask
GRANT SELECT, INSERT, UPDATE, DELETE, EXECUTE, SHOW VIEW
    ON agriauction.* TO 'agriauction_app'@'localhost';
```

`ON agriauction.*` is already narrower than `ON *.*`. The reporting account is narrower again: it cannot write.

`REVOKE` removes a privilege. `security.sql` revokes everything first, then grants only the intended set, so a re-run does not leave extra rights behind.

---

## 4. How to load and test

**1.** In Workbench, connected as `root`, run:

```sql
SET @app_password       = 'choose-a-strong-local-password';
SET @reporting_password = 'choose-a-strong-local-password';
SET @admin_password     = 'choose-a-strong-local-password';
```

If MySQL’s password policy is on, use at least 8 characters with mixed case, a number, and a symbol. Error 1819 means the password is too weak.

**2.** Run `database/security.sql` in the **same** session (user variables do not survive a reconnect).

**3.** Confirm grants (passwords are not displayed):

```sql
SHOW GRANTS FOR 'agriauction_app'@'localhost';
SHOW GRANTS FOR 'agriauction_reporting'@'localhost';
SHOW GRANTS FOR 'agriauction_admin'@'localhost';
```

**4.** Copy `@app_password` into `.env` as `DB_PASSWORD`. Never commit `.env`.

**5.** Prove the reporting account cannot write:

```sql
-- Connect as agriauction_reporting, then:
INSERT INTO depots (depot_code, depot_name, location, is_active)
VALUES ('TST', 'Should fail', 'Lusaka', 1);
-- Expected: ERROR 1142 (42000): INSERT command denied
```

**6.** Prove the app account cannot change the schema:

```sql
-- Connect as agriauction_app, then:
DROP TABLE bids;
-- Expected: ERROR 1142 (42000): DROP command denied
```

`FLUSH PRIVILEGES` is not required after `GRANT` on MySQL 8 (privileges apply immediately). Older tutorials still mention it.

---

## 5. Application vs database (keep this distinction for the viva)

- Staff login rows come from `seed.sql` / the staff table.
- Flask connects as `agriauction_app` using `.env` (Phase 7+).
- Page permissions use `@role_required` (VIEWER cannot open `/farmers/` even with the URL).
- Signed-in POST forms send a CSRF token (`app/csrf.py`).
- Real passwords are not stored in the repository.
