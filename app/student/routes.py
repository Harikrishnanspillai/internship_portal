# app/student/routes.py

from flask import Blueprint, render_template, session, redirect, url_for, request
from app.db import get_conn
import psycopg2.extras
import os
from werkzeug.utils import secure_filename

# configure uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")
ALLOWED_EXT = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


student_bp = Blueprint(
    'student',
    __name__,
    template_folder='templates'
)


# -------------------------
# Dashboard
# -------------------------
@student_bp.route('/student/dashboard')
def dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    student_id = session['user_id']

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Student core info
    cur.execute("""
        SELECT name, department, cgpa
        FROM Student
        WHERE student_id = %s
    """, (student_id,))
    info = cur.fetchone()

    # Application count
    cur.execute("""
        SELECT COUNT(*) AS count
        FROM Application
        WHERE student_id = %s
    """, (student_id,))
    app_count = cur.fetchone()["count"]

    # Documents summary
    cur.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) AS approved,
               SUM(CASE WHEN status = 'Rejected' THEN 1 ELSE 0 END) AS rejected,
               SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) AS pending
        FROM Document
        WHERE student_id = %s
    """, (student_id,))
    docs = cur.fetchone()

    # Visa info (latest)
    cur.execute("""
        SELECT country, application_status, issued_date, expiry_date
        FROM VisaPermit
        WHERE student_id = %s
        ORDER BY visa_id DESC LIMIT 1
    """, (student_id,))
    visa = cur.fetchone()

    # Housing info (latest)
    cur.execute("""
        SELECT h.location, h.room_type, h.rent, ha.allotment_date
        FROM HousingAssignment ha
        JOIN Housing h ON ha.housing_id = h.housing_id
        WHERE ha.student_id = %s
        ORDER BY ha.assign_id DESC LIMIT 1
    """, (student_id,))
    housing = cur.fetchone()

    cur.close()
    conn.close()

    return render_template(
        'student/dashboard.html',
        info=info,
        app_count=app_count,
        docs=docs,
        visa=visa,
        housing=housing
    )



# -------------------------
# Profile (View)
# -------------------------
@student_bp.route('/student/profile')
def profile():
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    student_id = session['user_id']

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT name, email, dob, department, cgpa
        FROM Student
        WHERE student_id = %s
    """, (student_id,))
    data = cur.fetchone()

    cur.close()
    conn.close()

    return render_template('student/profile.html', data=data)


# -------------------------
# Profile (Update)
# -------------------------
@student_bp.route('/student/profile/update', methods=['POST'])
def update_profile():
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    student_id = session['user_id']

    name = request.form['name']
    dob = request.form['dob']
    dept = request.form['department']
    cgpa = request.form['cgpa']

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE Student
        SET name = %s, dob = %s, department = %s, cgpa = %s
        WHERE student_id = %s
    """, (name, dob, dept, cgpa, student_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('student.profile'))


# -------------------------
# View Programs
# -------------------------
@student_bp.route('/student/programs')
def programs():
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT p.program_id, p.title,
               u.name AS university,
               m.name AS mentor,
               p.duration
        FROM Program p
        LEFT JOIN University u ON p.university_id = u.university_id
        LEFT JOIN Mentor m ON p.mentor_id = m.mentor_id
        ORDER BY p.program_id
    """)

    programs = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('student/view_programs.html', programs=programs)


# -------------------------
# Program Details
# -------------------------
@student_bp.route('/student/program/<int:pid>')
def program_details(pid):
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT p.title, p.description, p.eligibility, p.duration,
               p.start_date, p.end_date,
               u.name AS university,
               m.name AS mentor
        FROM Program p
        LEFT JOIN University u ON p.university_id = u.university_id
        LEFT JOIN Mentor m ON p.mentor_id = m.mentor_id
        WHERE p.program_id = %s
    """, (pid,))

    program = cur.fetchone()

    cur.close()
    conn.close()

    return render_template('student/program_details.html', program=program, pid=pid)


# -------------------------
# Apply to Program
# -------------------------
@student_bp.route('/student/program/<int:pid>/apply')
def apply(pid):
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    student_id = session['user_id']

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check existing
    cur.execute("""
        SELECT 1 FROM Application
        WHERE student_id = %s AND program_id = %s
    """, (student_id, pid))

    exists = cur.fetchone()

    if not exists:
        cur.execute("""
            INSERT INTO Application (student_id, program_id)
            VALUES (%s, %s)
        """, (student_id, pid))
        conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for('student.dashboard'))


# -------------------------
# Upload Documents (student)
# -------------------------
@student_bp.route('/student/upload_docs', methods=['GET','POST'])
def upload_docs():
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    student_id = session['user_id']
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            return render_template('student/upload_docs.html', error="No file selected.")
        filename = secure_filename(f.filename)
        if '.' not in filename or filename.rsplit('.',1)[1].lower() not in ALLOWED_EXT:
            return render_template('student/upload_docs.html', error="File type not allowed.")
        # store file
        dest = os.path.join(UPLOAD_FOLDER, filename)
        f.save(dest)
        # record in DB
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Document (student_id, file_name, file_type)
            VALUES (%s, %s, %s)
        """, (student_id, filename, filename.rsplit('.',1)[1].lower()))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('student.dashboard'))
    # GET
    return render_template('student/upload_docs.html')


# -------------------------
# Visa Application (student)
# -------------------------
@student_bp.route('/student/visa', methods=['GET','POST'])
def visa_application():
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))
    student_id = session['user_id']
    if request.method == 'POST':
        country = request.form.get('country')
        # optional: accept a supporting file
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO VisaPermit (student_id, country, application_status)
            VALUES (%s, %s, 'Pending')
        """, (student_id, country))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('student.dashboard'))
    # GET: show current visa (if any)
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT visa_id, country, application_status, issued_date, expiry_date FROM VisaPermit WHERE student_id = %s ORDER BY visa_id DESC LIMIT 1", (student_id,))
    visa = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('student/visa_application.html', visa=visa)


# -------------------------
# Housing Status (student)
# -------------------------
@student_bp.route('/student/housing')
def housing_status():
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))
    student_id = session['user_id']
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT h.location, h.room_type, h.rent, ha.allotment_date, ha.checkout_date
        FROM HousingAssignment ha
        JOIN Housing h ON ha.housing_id = h.housing_id
        WHERE ha.student_id = %s
        ORDER BY ha.assign_id DESC LIMIT 1
    """, (student_id,))
    assign = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('student/housing_status.html', assign=assign)
