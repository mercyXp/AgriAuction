# AgriAuction Digital Produce Trading Platform

AgriAuction is an **IT212 Database Management Systems** web application. Farmers register inspected produce lots at depots. Staff record bids from registered buyers on **OPEN** lots. Closing an auction creates at most one successful sale from the highest valid bid. Finance records payments and collections afterwards.

Money is shown in **ZMW**. Seed data is fictional Zambian names and places.

## Features

- Public landing, project brief, and staff login
- Role-based dashboard (ADMIN, OPERATOR, AUCTION_CLERK, FINANCE, VIEWER)
- Farmer and buyer CRUD (deactivate, never hard-delete history)
- Produce types, quality grades, and depots
- Lot registration, search, filter, open for auction
- Staff-placed bids with row locks
- Atomic auction close via `sp_close_auction`
- Sales list (sales are **not** typed in by hand)
- Payments via `sp_record_payment` (no overpay)
- Collections that mark sale and lot `COLLECTED` together
- SQL reports and Chart.js dashboard cards
- CSRF on signed-in POST forms, bcrypt passwords, parameterized SQL

## Technology stack

- HTML5, CSS3, Bootstrap 5, vanilla JavaScript, Jinja2
- Python 3.12 and Flask 3
- mysql-connector-python (no ORM)
- bcrypt, python-dotenv, Gunicorn
- MySQL 8 (InnoDB, utf8mb4)

## Architecture

```text
Browser
    ↓
Flask (Jinja pages + routes)
    ↓
MySQL (agriauction)
```

**Application users** live in table `staff` (who can open the website).  
**MySQL users** such as `agriauction_app` live in MySQL itself (who can run SQL). They are not the same thing. See `docs/security.md`.

## Local setup

1. Install **Python 3.12** and **MySQL 8**.
2. In the project folder:

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

3. Edit `.env`: set `SECRET_KEY` and `DB_PASSWORD` to the MySQL app-user password you create below.

## Database setup

In MySQL Workbench or the `mysql` client as **root**, run in this order (PowerShell example):

```powershell
Get-Content -Raw database\schema.sql, database\seed.sql, database\views.sql, database\procedures.sql, database\indexes.sql |
  & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

Or `SOURCE` each file:

1. `database/schema.sql` — tables, keys, CHECKs  
2. `database/seed.sql` — demo rows  
3. `database/views.sql`  
4. `database/procedures.sql`  
5. `database/indexes.sql`  
6. `database/security.sql` — set `@app_password`, `@reporting_password`, `@admin_password` **in the session** first (they are not in Git)

Copy the app password into `.env` as `DB_PASSWORD`. Use `DB_USER=agriauction_app`.

Windows service name is usually `MYSQL80` (`net start MYSQL80` as Administrator).

## Running the app

```bash
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). Staff login is **Get Started** → `/login`.

```bash
flask db-ping
python -m unittest discover -s tests
```

## Demo accounts

Coursework logins from `seed.sql` (not for a real deployment):

| Username | Password | Role |
|---|---|---|
| `chanda.admin` | `Admin#2026` | ADMIN |
| `mwansa.operator` | `Operator#2026` | OPERATOR |
| `tembo.clerk` | `Clerk#2026` | AUCTION_CLERK |
| `zulu.finance` | `Finance#2026` | FINANCE |
| `banda.viewer` | `Viewer#2026` | VIEWER |

`kabwe.archive` is inactive and cannot sign in.

## Railway deployment

See `docs/railway.md`. Start command:

```text
web: gunicorn --bind 0.0.0.0:$PORT run:app
```

Set `SECRET_KEY`, `FLASK_ENV=production`, `FLASK_DEBUG=0`, and MySQL `DB_*` or Railway `MYSQL*` variables. Never commit those values.

## Database concepts demonstrated

| Concept | Where |
|---|---|
| Normalization | `docs/normalization.md` |
| Joins | Views, reports, `database/queries.sql` |
| Subquery | Buyers above average spend in `queries.sql` |
| Views | `vw_auction_lot_summary`, `vw_sales_payment_summary` |
| Stored procedures | `sp_close_auction`, `sp_record_payment` |
| Transactions / ACID | `docs/transactions.md` |
| Indexes | `database/indexes.sql`, `docs/indexing.md` |
| Security | `docs/security.md`, CSRF, bcrypt, roles |
| Backup / recovery | `docs/backup-recovery.md` |

## Project documents

- `docs/erd.md` — entity-relationship notes  
- `docs/demonstration.md` — viva walk-through  
- `docs/final-audit.md` — assignment checklist  
- `docs/railway.md` — production env list  

## Security note

Never commit `.env`. Staff passwords are bcrypt hashes. SQL from the app uses `%s` parameters. Signed-in POST forms send a CSRF token. `FLASK_ENV=production` sets the session cookie `Secure` flag.
