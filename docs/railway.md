# Railway deployment

Production shape:

```text
Internet
   ↓
Railway Flask web service (Gunicorn)
   ↓
Railway MySQL
```

Flask serves HTML, CSS and JavaScript. There is no separate frontend service.

Live deploy from this workspace is **not** done here. Follow the checklist on your own Railway project.

---

## Start command

`Procfile`:

```text
web: gunicorn --bind 0.0.0.0:$PORT run:app
```

`run:app` is the Flask object created by `create_app()` in `run.py`. Gunicorn binds `0.0.0.0` and Railway’s `PORT`.

Do not run `python run.py` with debug on Railway.

---

## Environment variables (no secrets in Git)

Set these on the Flask service. Prefer Railway **reference variables** from the MySQL plugin instead of typing passwords.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Long random Flask session key (not the local `.env` value) |
| `FLASK_ENV` | `production` (turns on `SESSION_COOKIE_SECURE`, turns off debug) |
| `FLASK_DEBUG` | `0` |
| `DB_HOST` / `MYSQLHOST` | MySQL host |
| `DB_PORT` / `MYSQLPORT` | MySQL port |
| `DB_NAME` / `MYSQLDATABASE` | Database name |
| `DB_USER` / `MYSQLUSER` | App user (not `root` if you can avoid it) |
| `DB_PASSWORD` / `MYSQLPASSWORD` | App password |

`load_db_config()` accepts either `DB_*` or Railway `MYSQL*` names.

---

## First-time database load

Connect to Railway MySQL (plugin UI or a local mysql client with the public URL) and run, in order:

1. `database/schema.sql`
2. `database/seed.sql` (optional on production; useful for marking)
3. `database/views.sql`
4. `database/procedures.sql`
5. `database/indexes.sql`
6. Least-privilege users if you create them on that server (`database/security.sql`)

Then point `DB_USER` at a user that can `SELECT/INSERT/UPDATE/DELETE/EXECUTE/SHOW VIEW`.

---

## Production check (do this on Railway after deploy)

### Application

- [ ] `gunicorn` starts (no boot crash in logs)
- [ ] `$PORT` is used (do not hard-code 5000)
- [ ] `FLASK_ENV=production` and debug off

### Database

- [ ] Flask can `SELECT 1` (staff login works)
- [ ] Schema, views, procedures loaded
- [ ] Foreign keys reject invalid IDs

### Security

- [ ] Unique `SECRET_KEY`
- [ ] DB password not in Git
- [ ] Cookies Secure (HTTPS)

### Functionality

Login → Dashboard → farmer → buyer → lot → open → bid → close → sale → payment → collection → report → logout.
