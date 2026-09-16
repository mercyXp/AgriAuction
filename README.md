# AgriAuction Digital Produce Trading Platform

AgriAuction is a web application for an **IT212 Database Management Systems** project. Farmers register produce lots at depots. Buyers bid on open lots. When an auction closes, the highest valid bid becomes a successful sale. Payments and collections are recorded afterwards.

This repository is being built **phase by phase**. Phase 1 only starts the Flask application and a public home page.

## Technology stack

- HTML5, CSS3, Bootstrap 5, Jinja2
- Python 3 and Flask
- MySQL 8 (from Phase 2 onwards)
- Railway for later deployment

## Architecture

```text
Browser
    ↓
Flask (HTML pages + routes)
    ↓
MySQL (not connected yet in Phase 1)
```

## Local setup (Phase 1)

1. Install **Python 3.12** (or another Python 3 version).
2. Open a terminal in this project folder.
3. Create and activate a virtual environment:

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Copy environment variables:

```text
.env.example  →  .env
```

Change `SECRET_KEY` before any real deployment. Database values are placeholders until MySQL is set up.

5. Run the application:

```bash
python run.py
```

6. Open [http://localhost:5000](http://localhost:5000).

## What Phase 1 includes

- Flask application factory (`app/create_app`)
- Environment-based configuration
- Bootstrap layout and agricultural theme
- Home page
- Friendly 400, 403, 404, and 500 error pages
- Database *settings* only (no tables and no live queries yet)

## What comes next

Later phases add the MySQL schema, authentication, CRUD screens, bidding, auction closing, payments, reports, tests, and Railway deployment. Do not skip phases.

## Security note

Never commit `.env`. Real passwords and production keys stay in environment variables (local `.env` or Railway).
