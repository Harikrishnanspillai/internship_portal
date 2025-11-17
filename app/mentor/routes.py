# app/mentor/routes.py

from flask import Blueprint, render_template, session, redirect, url_for, request
from app.db import get_conn
import psycopg2.extras

mentor_bp = Blueprint(
    'mentor',
    __name__,
    template_folder='templates'
)

# -------------------------
# Mentor Dashboard
# -------------------------
@mentor_bp.route('/mentor/dashboard')
def dashboard():
    if session.get('role') != 'mentor':
        return redirect(url_for('main.login'))

    mentor_id = session['user_id']

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Mentor info
    cur.execute("""
        SELECT name, department
        FROM Mentor
        WHERE mentor_id = %s
    """, (mentor_id,))
    info = cur.fetchone()

    # Count programs
    cur.execute("""
        SELECT COUNT(*) AS count
        FROM Program
        WHERE mentor_id = %s
    """, (mentor_id,))
    program_count = cur.fetchone()["count"]

    # Count students in those programs
    cur.execute("""
        SELECT COUNT(*) AS count
        FROM Application a
        JOIN Program p ON a.program_id = p.program_id
        WHERE p.mentor_id = %s
    """, (mentor_id,))
    student_count = cur.fetchone()["count"]

    cur.close()
    conn.close()

    return render_template(
        'mentor/dashboard.html',
        info=info,
        program_count=program_count,
        student_count=student_count
    )


# -------------------------
# Mentor Profile
# -------------------------
@mentor_bp.route('/mentor/profile')
def profile():
    if session.get('role') != 'mentor':
        return redirect(url_for('main.login'))

    mentor_id = session['user_id']

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT name, email, department
        FROM Mentor
        WHERE mentor_id = %s
    """, (mentor_id,))
    data = cur.fetchone()

    cur.close()
    conn.close()

    return render_template('mentor/profile.html', data=data)


# -------------------------
# Mentor Profile Update
# -------------------------
@mentor_bp.route('/mentor/profile/update', methods=['POST'])
def update_profile():
    if session.get('role') != 'mentor':
        return redirect(url_for('main.login'))

    mentor_id = session['user_id']

    name = request.form['name']
    dept = request.form['department']

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE Mentor
        SET name = %s, department = %s
        WHERE mentor_id = %s
    """, (name, dept, mentor_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('mentor.profile'))


# -------------------------
# Assigned Students
# -------------------------
@mentor_bp.route('/mentor/students')
def students():
    if session.get('role') != 'mentor':
        return redirect(url_for('main.login'))

    mentor_id = session['user_id']

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT s.name AS student_name,
               s.email AS student_email,
               s.department AS student_dept,
               p.title AS program_title,
               a.status AS application_status
        FROM Application a
        JOIN Student s ON a.student_id = s.student_id
        JOIN Program p ON a.program_id = p.program_id
        WHERE p.mentor_id = %s
        ORDER BY p.title, s.name
    """, (mentor_id,))

    students = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('mentor/students.html', students=students)
