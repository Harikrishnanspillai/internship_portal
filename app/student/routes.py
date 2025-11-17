# app/student/routes.py

from flask import Blueprint, render_template, session, redirect, url_for, request
from app.db import get_conn
import psycopg2.extras

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

    # Student info
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

    cur.close()
    conn.close()

    return render_template(
        'student/dashboard.html',
        info=info,
        app_count=app_count
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
