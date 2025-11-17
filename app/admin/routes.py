from flask import Blueprint, render_template, session, redirect, url_for, request
from app.db import get_conn
import psycopg2.extras

admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="templates"
)

def guard():
    if session.get("role") != "admin":
        return False
    return True


# ----------------------------------
# ADMIN DASHBOARD
# ----------------------------------
@admin_bp.route("/admin/dashboard")
def dashboard():
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT COUNT(*) AS c FROM Student")
    student_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM Mentor")
    mentor_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM Program")
    program_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM Application")
    app_count = cur.fetchone()["c"]

    cur.close()
    conn.close()

    return render_template("admin/dashboard.html",
                           students=student_count,
                           mentors=mentor_count,
                           programs=program_count,
                           apps=app_count)


# ----------------------------------
# MANAGE STUDENTS (READ + DELETE)
# ----------------------------------
@admin_bp.route("/admin/students")
def manage_students():
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT student_id, name, email, department, cgpa
        FROM Student
        ORDER BY student_id
    """)
    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin/manage_students.html", data=data)


@admin_bp.route("/admin/students/delete/<int:sid>")
def delete_student(sid):
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM Student WHERE student_id = %s", (sid,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("admin.manage_students"))


# ----------------------------------
# MANAGE PROGRAMS (CREATE + READ + DELETE)
# ----------------------------------
@admin_bp.route("/admin/programs")
def manage_programs():
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT p.program_id, p.title, u.name AS university, m.name AS mentor
        FROM Program p
        LEFT JOIN University u ON p.university_id = u.university_id
        LEFT JOIN Mentor m ON p.mentor_id = m.mentor_id
        ORDER BY p.program_id
    """)
    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin/manage_programs.html", data=data)


@admin_bp.route("/admin/programs/create", methods=["POST"])
def create_program():
    if not guard():
        return redirect(url_for("main.login"))

    title = request.form["title"]
    university_id = request.form["university_id"]
    mentor_id = request.form["mentor_id"]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO Program (title, university_id, mentor_id)
        VALUES (%s, %s, %s)
    """, (title, university_id, mentor_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("admin.manage_programs"))


@admin_bp.route("/admin/programs/delete/<int:pid>")
def delete_program(pid):
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM Program WHERE program_id = %s", (pid,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("admin.manage_programs"))
