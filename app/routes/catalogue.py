"""Produce types, quality grades, and depots. Deactivate instead of delete."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from mysql.connector import errorcode

from app.auth import role_required
from app.database import MySQLError, execute, query_all, query_one
from app.helpers import next_code, parse_decimal

RECORD_ROLES = ("ADMIN", "OPERATOR")

produce_bp = Blueprint("produce", __name__, url_prefix="/produce")
grades_bp = Blueprint("grades", __name__, url_prefix="/grades")
depots_bp = Blueprint("depots", __name__, url_prefix="/depots")


def _list_rows(table, search_sql, params, extra=""):
    try:
        return query_all(search_sql + extra, params)
    except RuntimeError:
        flash("Cannot reach the database. Check MySQL and .env.", "danger")
        return []


@produce_bp.route("/")
@role_required(*RECORD_ROLES)
def index():
    q = (request.args.get("q") or "").strip()
    like = f"%{q}%"
    rows = _list_rows(
        "produce_types",
        """
        SELECT produce_type_id, name, description, unit_of_measure, is_active
        FROM produce_types
        WHERE (%s = '' OR name LIKE %s OR unit_of_measure LIKE %s)
        ORDER BY name
        """,
        (q, like, like),
    )
    return render_template("produce/index.html", rows=rows, q=q)


@produce_bp.route("/create", methods=["GET", "POST"])
@role_required(*RECORD_ROLES)
def create():
    form = {"name": "", "description": "", "unit_of_measure": "tonne"}
    errors = {}
    if request.method == "POST":
        form, errors = _validate_produce(request.form)
        if not errors:
            try:
                produce_id, _ = execute(
                    """
                    INSERT INTO produce_types (name, description, unit_of_measure, is_active)
                    VALUES (%s, %s, %s, 1)
                    """,
                    (form["name"], form["description"], form["unit_of_measure"]),
                )
            except MySQLError as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    errors["name"] = "That produce type already exists."
                else:
                    flash("Could not save the produce type.", "danger")
            else:
                flash("Produce type was added.", "success")
                return redirect(url_for("produce.edit", produce_type_id=produce_id))
    return render_template("produce/form.html", form=form, errors=errors, mode="create")


@produce_bp.route("/<int:produce_type_id>/edit", methods=["GET", "POST"])
@role_required(*RECORD_ROLES)
def edit(produce_type_id):
    row = query_one(
        "SELECT * FROM produce_types WHERE produce_type_id = %s",
        (produce_type_id,),
    )
    if row is None:
        flash("Produce type not found.", "warning")
        return redirect(url_for("produce.index"))
    form = {
        "name": row["name"],
        "description": row["description"] or "",
        "unit_of_measure": row["unit_of_measure"],
    }
    errors = {}
    if request.method == "POST":
        form, errors = _validate_produce(request.form)
        if not errors:
            try:
                execute(
                    """
                    UPDATE produce_types
                    SET name = %s, description = %s, unit_of_measure = %s
                    WHERE produce_type_id = %s
                    """,
                    (form["name"], form["description"], form["unit_of_measure"], produce_type_id),
                )
            except MySQLError as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    errors["name"] = "That produce type already exists."
                else:
                    flash("Could not update the produce type.", "danger")
            else:
                flash("Produce type was updated.", "success")
                return redirect(url_for("produce.index"))
    return render_template(
        "produce/form.html",
        form=form,
        errors=errors,
        mode="edit",
        row=row,
    )


@produce_bp.route("/<int:produce_type_id>/deactivate", methods=["POST"])
@role_required(*RECORD_ROLES)
def deactivate(produce_type_id):
    execute(
        "UPDATE produce_types SET is_active = 0 WHERE produce_type_id = %s",
        (produce_type_id,),
    )
    flash("Produce type was deactivated. Existing lots were kept.", "success")
    return redirect(url_for("produce.index"))


@produce_bp.route("/<int:produce_type_id>/reactivate", methods=["POST"])
@role_required(*RECORD_ROLES)
def reactivate(produce_type_id):
    execute(
        "UPDATE produce_types SET is_active = 1 WHERE produce_type_id = %s",
        (produce_type_id,),
    )
    flash("Produce type is active again.", "success")
    return redirect(url_for("produce.index"))


def _validate_produce(form):
    errors = {}
    data = {
        "name": (form.get("name") or "").strip(),
        "description": (form.get("description") or "").strip() or None,
        "unit_of_measure": (form.get("unit_of_measure") or "").strip(),
    }
    if len(data["name"]) < 2:
        errors["name"] = "Enter a produce name."
    if len(data["unit_of_measure"]) < 1:
        errors["unit_of_measure"] = "Enter a unit (for example tonne or bag)."
    return data, errors


@grades_bp.route("/")
@role_required("ADMIN")
def index():
    q = (request.args.get("q") or "").strip()
    like = f"%{q}%"
    rows = _list_rows(
        "quality_grades",
        """
        SELECT grade_id, grade_code, grade_name, description, is_active
        FROM quality_grades
        WHERE (%s = '' OR grade_code LIKE %s OR grade_name LIKE %s)
        ORDER BY grade_code
        """,
        (q, like, like),
    )
    return render_template("grades/index.html", rows=rows, q=q)


@grades_bp.route("/create", methods=["GET", "POST"])
@role_required("ADMIN")
def create():
    form = {"grade_code": "", "grade_name": "", "description": ""}
    errors = {}
    if request.method == "POST":
        form, errors = _validate_grade(request.form)
        if not errors:
            try:
                execute(
                    """
                    INSERT INTO quality_grades (grade_code, grade_name, description, is_active)
                    VALUES (%s, %s, %s, 1)
                    """,
                    (form["grade_code"], form["grade_name"], form["description"]),
                )
            except MySQLError as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    errors["grade_code"] = "That grade code already exists."
                else:
                    flash("Could not save the grade.", "danger")
            else:
                flash("Quality grade was added.", "success")
                return redirect(url_for("grades.index"))
    return render_template("grades/form.html", form=form, errors=errors, mode="create")


@grades_bp.route("/<int:grade_id>/edit", methods=["GET", "POST"])
@role_required("ADMIN")
def edit(grade_id):
    row = query_one("SELECT * FROM quality_grades WHERE grade_id = %s", (grade_id,))
    if row is None:
        flash("Grade not found.", "warning")
        return redirect(url_for("grades.index"))
    form = {
        "grade_code": row["grade_code"],
        "grade_name": row["grade_name"],
        "description": row["description"] or "",
    }
    errors = {}
    if request.method == "POST":
        form, errors = _validate_grade(request.form)
        if not errors:
            try:
                execute(
                    """
                    UPDATE quality_grades
                    SET grade_code = %s, grade_name = %s, description = %s
                    WHERE grade_id = %s
                    """,
                    (form["grade_code"], form["grade_name"], form["description"], grade_id),
                )
            except MySQLError as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    errors["grade_code"] = "That grade code already exists."
                else:
                    flash("Could not update the grade.", "danger")
            else:
                flash("Quality grade was updated.", "success")
                return redirect(url_for("grades.index"))
    return render_template("grades/form.html", form=form, errors=errors, mode="edit", row=row)


@grades_bp.route("/<int:grade_id>/deactivate", methods=["POST"])
@role_required("ADMIN")
def deactivate(grade_id):
    execute("UPDATE quality_grades SET is_active = 0 WHERE grade_id = %s", (grade_id,))
    flash("Grade was deactivated. Existing lots were kept.", "success")
    return redirect(url_for("grades.index"))


@grades_bp.route("/<int:grade_id>/reactivate", methods=["POST"])
@role_required("ADMIN")
def reactivate(grade_id):
    execute("UPDATE quality_grades SET is_active = 1 WHERE grade_id = %s", (grade_id,))
    flash("Grade is active again.", "success")
    return redirect(url_for("grades.index"))


def _validate_grade(form):
    errors = {}
    data = {
        "grade_code": (form.get("grade_code") or "").strip().upper(),
        "grade_name": (form.get("grade_name") or "").strip(),
        "description": (form.get("description") or "").strip() or None,
    }
    if len(data["grade_code"]) < 1:
        errors["grade_code"] = "Enter a grade code."
    if len(data["grade_name"]) < 2:
        errors["grade_name"] = "Enter a grade name."
    return data, errors


@depots_bp.route("/")
@role_required(*RECORD_ROLES)
def index():
    q = (request.args.get("q") or "").strip()
    like = f"%{q}%"
    rows = _list_rows(
        "depots",
        """
        SELECT depot_id, depot_code, depot_name, location, capacity, is_active
        FROM depots
        WHERE (%s = '' OR depot_code LIKE %s OR depot_name LIKE %s OR location LIKE %s)
        ORDER BY depot_name
        """,
        (q, like, like, like),
    )
    return render_template("depots/index.html", rows=rows, q=q)


@depots_bp.route("/create", methods=["GET", "POST"])
@role_required(*RECORD_ROLES)
def create():
    form = {"depot_name": "", "location": "", "capacity": ""}
    errors = {}
    if request.method == "POST":
        form, errors = _validate_depot(request.form)
        if not errors:
            code = next_code("depots", "depot_code", "DPT-")
            try:
                execute(
                    """
                    INSERT INTO depots (depot_code, depot_name, location, capacity, is_active)
                    VALUES (%s, %s, %s, %s, 1)
                    """,
                    (code, form["depot_name"], form["location"], form["capacity"]),
                )
            except MySQLError as err:
                if err.errno == errorcode.ER_DUP_ENTRY:
                    flash("That depot code is already in use. Try again.", "danger")
                else:
                    flash("Could not save the depot.", "danger")
            else:
                flash(f"Depot {code} was added.", "success")
                return redirect(url_for("depots.index"))
    return render_template("depots/form.html", form=form, errors=errors, mode="create")


@depots_bp.route("/<int:depot_id>/edit", methods=["GET", "POST"])
@role_required(*RECORD_ROLES)
def edit(depot_id):
    row = query_one("SELECT * FROM depots WHERE depot_id = %s", (depot_id,))
    if row is None:
        flash("Depot not found.", "warning")
        return redirect(url_for("depots.index"))
    form = {
        "depot_name": row["depot_name"],
        "location": row["location"],
        "capacity": str(row["capacity"]),
    }
    errors = {}
    if request.method == "POST":
        form, errors = _validate_depot(request.form)
        if not errors:
            execute(
                """
                UPDATE depots
                SET depot_name = %s, location = %s, capacity = %s
                WHERE depot_id = %s
                """,
                (form["depot_name"], form["location"], form["capacity"], depot_id),
            )
            flash("Depot was updated.", "success")
            return redirect(url_for("depots.index"))
    return render_template("depots/form.html", form=form, errors=errors, mode="edit", row=row)


@depots_bp.route("/<int:depot_id>/deactivate", methods=["POST"])
@role_required(*RECORD_ROLES)
def deactivate(depot_id):
    execute("UPDATE depots SET is_active = 0 WHERE depot_id = %s", (depot_id,))
    flash("Depot was deactivated. Existing lots were kept.", "success")
    return redirect(url_for("depots.index"))


@depots_bp.route("/<int:depot_id>/reactivate", methods=["POST"])
@role_required(*RECORD_ROLES)
def reactivate(depot_id):
    execute("UPDATE depots SET is_active = 1 WHERE depot_id = %s", (depot_id,))
    flash("Depot is active again.", "success")
    return redirect(url_for("depots.index"))


def _validate_depot(form):
    errors = {}
    capacity = parse_decimal(form.get("capacity"), "capacity", errors, minimum=0)
    data = {
        "depot_name": (form.get("depot_name") or "").strip(),
        "location": (form.get("location") or "").strip(),
        "capacity": capacity,
    }
    if len(data["depot_name"]) < 2:
        errors["depot_name"] = "Enter a depot name."
    if len(data["location"]) < 2:
        errors["location"] = "Enter a location."
    return data, errors
