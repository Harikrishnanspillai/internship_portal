from flask import Blueprint, render_template, session, redirect, url_for, request, send_from_directory
from app.db import get_conn
import psycopg2.extras
import os

mentor_bp = Blueprint(
    "mentor",
    __name__,
    template_folder="templates"
)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")


def guard():
    return session.get("role") == "mentor"





@mentor_bp.route('/mentor/dashboard')
def dashboard():
    if not guard():
        return redirect(url_for("main.login"))

    mentor_id = session["user_id"]

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    
    cur.execute("SELECT COUNT(*) FROM Program WHERE mentor_id=%s", (mentor_id,))
    program_count = cur.fetchone()[0]

    
    cur.execute("""
        SELECT COUNT(*)
        FROM ApplicationDocument ad
        JOIN Application a ON ad.application_id = a.application_id
        JOIN Program p ON a.program_id = p.program_id
        WHERE p.mentor_id=%s AND ad.status='Pending'
    """, (mentor_id,))
    pending_docs = cur.fetchone()[0]

    
    cur.execute("""
        SELECT COUNT(*)
        FROM ScholarshipApplication sa
        JOIN Application a ON sa.application_id = a.application_id
        JOIN Program p ON a.program_id = p.program_id
        WHERE p.mentor_id=%s AND sa.status='Pending'
    """, (mentor_id,))
    pending_sch = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "mentor/dashboard.html",
        programs=program_count,
        pending_docs=pending_docs,
        pending_sch=pending_sch
    )





@mentor_bp.route('/mentor/student_applications')
def student_applications():
    if not guard():
        return redirect(url_for("main.login"))

    mentor_id = session["user_id"]
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT a.application_id, s.student_id, s.name AS student_name,
               s.email, p.title AS program_title, a.status
        FROM Application a
        JOIN Student s ON a.student_id = s.student_id
        JOIN Program p ON a.program_id = p.program_id
        WHERE p.mentor_id = %s
        ORDER BY a.application_id DESC
    """, (mentor_id,))
    apps = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("mentor/student_applications.html", apps=apps)





@mentor_bp.route('/mentor/application/<int:app_id>')
def review_application(app_id):
    if not guard():
        return redirect(url_for("main.login"))

    mentor_id = session["user_id"]

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    
    cur.execute("""
        SELECT p.mentor_id, p.title, s.name AS student_name
        FROM Application a
        JOIN Program p ON a.program_id = p.program_id
        JOIN Student s ON a.student_id = s.student_id
        WHERE a.application_id=%s
    """, (app_id,))
    row = cur.fetchone()

    if not row or row["mentor_id"] != mentor_id:
        cur.close()
        conn.close()
        return "Unauthorized", 403

    program_title = row["title"]
    student_name = row["student_name"]

    
    cur.execute("""
        SELECT rd.req_id, rd.document_name,
               ad.file_name, ad.status
        FROM RequiredDocuments rd
        LEFT JOIN ApplicationDocument ad
        ON rd.req_id = ad.req_id AND ad.application_id=%s
        WHERE rd.program_id = (
            SELECT program_id FROM Application WHERE application_id=%s
        )
        ORDER BY rd.req_id
    """, (app_id, app_id))
    docs = cur.fetchall()

    
    cur.execute("""
        SELECT sa.sch_app_id, sa.status,
               sc.name, sc.amount
        FROM ScholarshipApplication sa
        JOIN Scholarship sc ON sa.scholarship_id = sc.scholarship_id
        WHERE sa.application_id=%s
    """, (app_id,))
    sch = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "mentor/review_application.html",
        app_id=app_id,
        program_title=program_title,
        student_name=student_name,
        docs=docs,
        sch=sch
    )





@mentor_bp.route('/mentor/document/<int:app_id>/<int:req_id>/<string:action>', methods=['POST'])
def decide_document(app_id, req_id, action):
    if not guard():
        return redirect(url_for("main.login"))

    if action not in ("approve", "reject"):
        return redirect(url_for('mentor.review_application', app_id=app_id))

    status = "Approved" if action == "approve" else "Rejected"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE ApplicationDocument
        SET status=%s
        WHERE application_id=%s AND req_id=%s
    """, (status, app_id, req_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('mentor.review_application', app_id=app_id))





@mentor_bp.route('/mentor/scholarship/<int:sch_id>/<string:action>', methods=['POST'])
def decide_scholarship(sch_id, action):
    if not guard():
        return redirect(url_for("main.login"))

    if action not in ("approve", "reject"):
        return redirect(request.referrer)

    status = "Approved" if action == "approve" else "Rejected"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE ScholarshipApplication
        SET status=%s
        WHERE sch_app_id=%s
    """, (status, sch_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(request.referrer)

@mentor_bp.route('/mentor/review_documents')
def review_documents():
    if not guard():
        return redirect(url_for("main.login"))

    mentor_id = session["user_id"]
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT ad.application_id, ad.req_id, ad.file_name, ad.status,
               rd.document_name,
               s.name AS student_name, p.title AS program_title
        FROM ApplicationDocument ad
        JOIN RequiredDocuments rd ON ad.req_id = rd.req_id
        JOIN Application a ON ad.application_id = a.application_id
        JOIN Student s ON a.student_id = s.student_id
        JOIN Program p ON a.program_id = p.program_id
        WHERE p.mentor_id=%s
        ORDER BY ad.status DESC, ad.application_id DESC
    """, (mentor_id,))
    docs = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("mentor/review_documents.html", docs=docs)

@mentor_bp.route('/mentor/review_scholarships')
def review_scholarships():
    if not guard():
        return redirect(url_for("main.login"))

    mentor_id = session["user_id"]
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT sa.sch_app_id, sa.status,
               sc.name AS scholarship,
               sc.amount,
               s.name AS student_name,
               p.title AS program_title
        FROM ScholarshipApplication sa
        JOIN Application a ON sa.application_id = a.application_id
        JOIN Student s ON a.student_id = s.student_id
        JOIN Program p ON a.program_id = p.program_id
        JOIN Scholarship sc ON sa.scholarship_id = sc.scholarship_id
        WHERE p.mentor_id=%s
        ORDER BY sa.sch_app_id DESC
    """, (mentor_id,))
    sch = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("mentor/review_scholarships.html", sch=sch)
@mentor_bp.route('/mentor/assigned_students')
def assigned_students():
    if not guard():
        return redirect(url_for("main.login"))

    mentor_id = session["user_id"]

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT s.student_id, s.name, s.email, s.department, s.cgpa,
               p.title AS program_title
        FROM Application a
        JOIN Student s ON a.student_id = s.student_id
        JOIN Program p ON a.program_id = p.program_id
        WHERE p.mentor_id=%s
        ORDER BY s.student_id
    """, (mentor_id,))
    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("mentor/assigned_students.html", students=students)
