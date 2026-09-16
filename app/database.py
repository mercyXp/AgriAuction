"""MySQL connection helpers for AgriAuction.

Flask opens one connection per request (get_db) and closes it when the
request ends (close_db). Passwords come from the environment, never from
source code.

Every SQL statement must be parameterized. Pass values in a tuple:

    query_one("SELECT * FROM farmers WHERE farmer_id = %s", (farmer_id,))

Do not build SQL with f-strings or + concatenation of user input.
"""

import os

import mysql.connector
from flask import current_app, g
from mysql.connector import Error as MySQLError


def load_db_config():
    """Read MySQL settings from the environment."""
    return {
        "DB_HOST": os.getenv("DB_HOST", "localhost"),
        "DB_PORT": int(os.getenv("DB_PORT", "3306")),
        "DB_NAME": os.getenv("DB_NAME", "agriauction"),
        "DB_USER": os.getenv("DB_USER", "agriauction_app"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD", ""),
    }


def init_app(app):
    """Register connection cleanup and the db-ping CLI command."""
    app.teardown_appcontext(close_db)

    @app.cli.command("db-ping")
    def db_ping_command():
        """Test that Flask can connect to MySQL."""
        import click

        try:
            ok = ping_db()
        except RuntimeError as err:
            click.echo(f"MySQL connection failed: {err}", err=True)
            raise SystemExit(1)

        if ok:
            click.echo("MySQL connection OK")


def get_db():
    """Return the MySQL connection for this request. Open one if needed."""
    if "db" not in g:
        try:
            g.db = mysql.connector.connect(
                host=current_app.config["DB_HOST"],
                port=int(current_app.config["DB_PORT"]),
                database=current_app.config["DB_NAME"],
                user=current_app.config["DB_USER"],
                password=current_app.config["DB_PASSWORD"],
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
                autocommit=False,
                connection_timeout=8,
            )
        except MySQLError as err:
            g.pop("db", None)
            raise RuntimeError(
                f"Could not connect to MySQL ({err.errno}): {err.msg}"
            ) from err
    return g.db


def close_db(error=None):
    """Close the request connection if one was opened."""
    db = g.pop("db", None)
    if db is None:
        return
    try:
        if db.is_connected():
            db.close()
    except MySQLError:
        pass


def _params(params):
    """Require a tuple/list/dict so a single value is not passed by accident."""
    if params is None:
        return ()
    if not isinstance(params, (tuple, list, dict)):
        raise TypeError(
            "SQL params must be a tuple, list, or dict. "
            "Example: (farmer_id,) not farmer_id"
        )
    return params


def query_all(sql, params=()):
    """Run a SELECT and return all rows as dictionaries."""
    params = _params(params)
    cursor = get_db().cursor(dictionary=True, buffered=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()


def query_one(sql, params=()):
    """Run a SELECT and return one row as a dictionary, or None."""
    params = _params(params)
    cursor = get_db().cursor(dictionary=True, buffered=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()


def execute(sql, params=(), commit=True):
    """Run INSERT, UPDATE, or DELETE.

    Returns (lastrowid, rowcount). Set commit=False to take part in a
    larger transaction and call get_db().commit() yourself.
    """
    params = _params(params)
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(sql, params)
        lastrowid = cursor.lastrowid
        rowcount = cursor.rowcount
        if commit:
            db.commit()
        return lastrowid, rowcount
    except MySQLError:
        db.rollback()
        raise
    finally:
        cursor.close()


def ping_db():
    """Return True if SELECT 1 succeeds on the current connection."""
    row = query_one("SELECT 1 AS ok", ())
    return row is not None and row["ok"] == 1
