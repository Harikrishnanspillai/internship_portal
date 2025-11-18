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

    # Total counts
    cur.execute("SELECT COUNT(*) AS c FROM Student")
    student_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM Mentor")
    mentor_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM Program")
    program_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM Application")
    application_count = cur.fetchone()["c"]

    # Documents pending
    cur.execute("SELECT COUNT(*) AS c FROM Document WHERE status = 'Pending'")
    docs_pending = cur.fetchone()["c"]

    # Visa pending
    cur.execute("SELECT COUNT(*) AS c FROM VisaPermit WHERE application_status = 'Pending'")
    visa_pending = cur.fetchone()["c"]

    # Housing available
    cur.execute("SELECT COUNT(*) AS c FROM Housing WHERE availability = TRUE")
    housing_available = cur.fetchone()["c"]

    # Scholarships
    cur.execute("SELECT COUNT(*) AS c FROM Scholarship")
    scholarship_count = cur.fetchone()["c"]

    cur.close()
    conn.close()

    return render_template(
        "admin/dashboard.html",
        students=student_count,
        mentors=mentor_count,
        programs=program_count,
        apps=application_count,
        docs_pending=docs_pending,
        visa_pending=visa_pending,
        housing_available=housing_available,
        scholarship_count=scholarship_count
    )



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


# -------------------------
# Manage Visa Applications
# -------------------------
@admin_bp.route('/admin/visa')
def manage_visa():
    if not guard():
        return redirect(url_for('main.login'))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT v.visa_id, v.student_id, s.name AS student_name, v.country, v.application_status, v.issued_date, v.expiry_date
        FROM VisaPermit v
        JOIN Student s ON v.student_id = s.student_id
        ORDER BY v.visa_id DESC
    """)
    visas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/manage_visa.html', visas=visas)


@admin_bp.route('/admin/visa/decide/<int:vid>', methods=['POST'])
def decide_visa(vid):
    if not guard():
        return redirect(url_for('main.login'))
    action = request.form.get('action')  # 'approve' or 'reject'
    conn = get_conn()
    cur = conn.cursor()
    if action == 'approve':
        # set status and optionally set issued/expiry dates (simple)
        cur.execute("UPDATE VisaPermit SET application_status = 'Approved', issued_date = CURRENT_DATE, expiry_date = (CURRENT_DATE + INTERVAL '1 year') WHERE visa_id = %s", (vid,))
    else:
        cur.execute("UPDATE VisaPermit SET application_status = 'Rejected' WHERE visa_id = %s", (vid,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin.manage_visa'))


# -------------------------
# Manage Scholarships
# (Read + Create + Delete)
# -------------------------
@admin_bp.route('/admin/scholarships')
def manage_scholarships():
    if not guard():
        return redirect(url_for('main.login'))
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT s.scholarship_id, s.name, s.amount, p.title AS program_title
        FROM Scholarship s
        LEFT JOIN Program p ON s.program_id = p.program_id
        ORDER BY s.scholarship_id DESC
    """)
    scholarships = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/manage_scholarships.html', scholarships=scholarships)

@admin_bp.route('/admin/scholarships/create', methods=['POST'])
def create_scholarship():
    if not guard():
        return redirect(url_for('main.login'))
    program_id = request.form['program_id']
    name = request.form['name']
    amount = request.form['amount'] or None
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO Scholarship (program_id, name, amount) VALUES (%s,%s,%s)", (program_id, name, amount))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin.manage_scholarships'))

@admin_bp.route('/admin/scholarships/delete/<int:sid>')
def delete_scholarship(sid):
    if not guard():
        return redirect(url_for('main.login'))
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM Scholarship WHERE scholarship_id = %s", (sid,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin.manage_scholarships'))


# -------------------------
# Manage Housing
# (Create listing + Assign + Delete)
# -------------------------
@admin_bp.route('/admin/housing')
def manage_housing():
    if not guard():
        return redirect(url_for('main.login'))
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT h.housing_id, u.name AS university, h.location, h.room_type, h.rent, h.availability
        FROM Housing h
        LEFT JOIN University u ON h.university_id = u.university_id
        ORDER BY h.housing_id DESC
    """)
    houses = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin/manage_housing.html', houses=houses)

@admin_bp.route('/admin/housing/create', methods=['POST'])
def create_housing():
    if not guard():
        return redirect(url_for('main.login'))
    university_id = request.form['university_id']
    location = request.form['location']
    room_type = request.form['room_type']
    rent = request.form['rent'] or None
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO Housing (university_id, location, room_type, rent) VALUES (%s,%s,%s,%s)", (university_id, location, room_type, rent))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin.manage_housing'))

@admin_bp.route('/admin/housing/assign', methods=['POST'])
def assign_housing():
    if not guard():
        return redirect(url_for('main.login'))
    student_id = request.form['student_id']
    housing_id = request.form['housing_id']
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO HousingAssignment (student_id, housing_id) VALUES (%s,%s)", (student_id, housing_id))
    # optionally mark availability false
    cur.execute("UPDATE Housing SET availability = FALSE WHERE housing_id = %s", (housing_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('admin.manage_housing'))
