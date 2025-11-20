from flask import Blueprint, render_template, session, redirect, url_for, request
from app.db import get_conn
import psycopg2.extras
from werkzeug.security import generate_password_hash

admin_bp = Blueprint("admin", __name__, template_folder="templates")


def guard():
    return session.get("role") == "admin"


# -------------------------
# DASHBOARD
# -------------------------
@admin_bp.route("/admin/dashboard")
def dashboard():
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT COUNT(*) FROM Student")
    student_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Mentor")
    mentor_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Program")
    program_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Application")
    application_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM ApplicationDocument WHERE status='Pending'")
    docs_pending = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM VisaPermit WHERE application_status='Pending'")
    visa_pending = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Housing WHERE availability=TRUE")
    housing_available = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Scholarship")
    scholarship_count = cur.fetchone()[0]

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


# -------------------------
# MANAGE STUDENTS
# -------------------------
@admin_bp.route("/admin/students")
def manage_students():
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT student_id, name, email, department, cgpa FROM Student ORDER BY student_id")
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
    cur.execute("DELETE FROM Student WHERE student_id=%s", (sid,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("admin.manage_students"))


# -------------------------
# MANAGE PROGRAMS
# -------------------------
@admin_bp.route("/admin/programs")
def manage_programs():
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT 
            p.program_id,
            p.title,
            u.name AS university,
            m.name AS mentor,
            p.duration,
            p.start_date,
            p.end_date
        FROM Program p
        LEFT JOIN University u ON p.university_id = u.university_id
        LEFT JOIN Mentor m ON p.mentor_id = m.mentor_id
        ORDER BY p.program_id;
    """)
    programs = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("admin/manage_programs.html", data=programs)


@admin_bp.route("/admin/programs/create", methods=["POST"])
def create_program():
    if not guard():
        return redirect(url_for("main.login"))

    title = request.form["title"]
    university_id = request.form["university_id"]
    mentor_id = request.form["mentor_id"]

    description = request.form.get("description")
    eligibility = request.form.get("eligibility")
    duration = request.form.get("duration") or None
    start_date = request.form.get("start_date") or None
    end_date = request.form.get("end_date") or None

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO Program
        (title, description, eligibility, duration, start_date, end_date,
         university_id, mentor_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        title, description, eligibility, duration,
        start_date, end_date, university_id, mentor_id
    ))

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
    cur.execute("DELETE FROM Program WHERE program_id=%s", (pid,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("admin.manage_programs"))


# -------------------------
# MANAGE SCHOLARSHIPS
# -------------------------
@admin_bp.route('/admin/scholarships')
def manage_scholarships():
    if not guard():
        return redirect(url_for('main.login'))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT 
            s.scholarship_id,
            s.name,
            s.amount,
            s.eligibility_criteria,
            p.title AS program_title
        FROM Scholarship s
        JOIN Program p ON s.program_id = p.program_id
        ORDER BY s.scholarship_id DESC;
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
    eligibility = request.form.get('eligibility_criteria')

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO Scholarship (program_id, name, amount, eligibility_criteria)
        VALUES (%s, %s, %s, %s)
    """, (program_id, name, amount, eligibility))

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
    cur.execute("DELETE FROM Scholarship WHERE scholarship_id=%s", (sid,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('admin.manage_scholarships'))


# -------------------------
# MANAGE VISA
# -------------------------
@admin_bp.route('/admin/visa')
def manage_visa():
    if not guard():
        return redirect(url_for('main.login'))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT v.visa_id, v.student_id, s.name AS student_name,
               v.country, v.application_status, v.issued_date, v.expiry_date
        FROM VisaPermit v
        JOIN Student s ON v.student_id = s.student_id
        ORDER BY v.visa_id DESC
    """)
    visas = cur.fetchall()

    cur.close()
    conn.close()
    return render_template('admin/manage_visa.html', visas=visas)


@admin_bp.route('/admin/visa/<int:vid>/<string:action>', methods=['POST'])
def decide_visa(vid, action):
    if not guard():
        return redirect(url_for('main.login'))

    if action not in ("approve", "reject"):
        return redirect(url_for('admin.manage_visa'))

    conn = get_conn()
    cur = conn.cursor()

    if action == "approve":
        cur.execute("""
            UPDATE VisaPermit
            SET application_status='Approved',
                issued_date=CURRENT_DATE,
                expiry_date=CURRENT_DATE + INTERVAL '365 days'
            WHERE visa_id=%s
        """, (vid,))
    else:
        cur.execute("""
            UPDATE VisaPermit
            SET application_status='Rejected'
            WHERE visa_id=%s
        """, (vid,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('admin.manage_visa'))


# -------------------------
# MANAGE HOUSING (LIST + CREATE)
# -------------------------
@admin_bp.route('/admin/housing')
def manage_housing():
    if not guard():
        return redirect(url_for('main.login'))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT h.housing_id, u.name AS university, h.location,
               h.room_type, h.rent, h.availability
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
    cur.execute("""
        INSERT INTO Housing (university_id, location, room_type, rent)
        VALUES (%s, %s, %s, %s)
    """, (university_id, location, room_type, rent))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('admin.manage_housing'))


# -------------------------
# HOUSING REQUEST WORKFLOW
# -------------------------
@admin_bp.route('/admin/housing/requests')
def housing_requests():
    if not guard():
        return redirect(url_for('main.login'))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT hr.request_id, hr.request_type, hr.status, hr.request_date,
               s.student_id, s.name AS student_name
        FROM HousingRequest hr
        JOIN Student s ON hr.student_id = s.student_id
        ORDER BY hr.request_date DESC
    """)
    reqs = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin/housing_requests.html", reqs=reqs)


@admin_bp.route('/admin/housing/requests/<int:req_id>/<string:action>', methods=['POST'])
def decide_housing_request(req_id, action):
    if not guard():
        return redirect(url_for('main.login'))

    if action not in ("approve", "reject"):
        return redirect(url_for('admin.housing_requests'))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT request_id, student_id, request_type
        FROM HousingRequest
        WHERE request_id=%s
    """, (req_id,))
    req = cur.fetchone()

    if not req:
        cur.close()
        conn.close()
        return redirect(url_for('admin.housing_requests'))

    student_id = req["student_id"]
    req_type = req["request_type"]

    if action == "reject":
        cur.execute("UPDATE HousingRequest SET status='Rejected' WHERE request_id=%s", (req_id,))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('admin.housing_requests'))

    if req_type == "apply":
        cur.execute("SELECT housing_id FROM Housing WHERE availability=TRUE LIMIT 1")
        available = cur.fetchone()

        if not available:
            cur.execute("UPDATE HousingRequest SET status='Rejected' WHERE request_id=%s", (req_id,))
        else:
            housing_id = available["housing_id"]

            cur.execute("""
                INSERT INTO HousingAssignment (student_id, housing_id)
                VALUES (%s,%s)
            """, (student_id, housing_id))

            cur.execute("UPDATE Housing SET availability=FALSE WHERE housing_id=%s", (housing_id,))

            cur.execute("UPDATE HousingRequest SET status='Approved' WHERE request_id=%s", (req_id,))

    else:
        cur.execute("""
            UPDATE HousingAssignment
            SET checkout_date=CURRENT_DATE
            WHERE student_id=%s AND checkout_date IS NULL
        """, (student_id,))

        cur.execute("""
            UPDATE Housing SET availability=TRUE
            WHERE housing_id IN (
                SELECT housing_id FROM HousingAssignment
                WHERE student_id=%s
                ORDER BY assign_id DESC LIMIT 1
            )
        """, (student_id,))

        cur.execute("UPDATE HousingRequest SET status='Approved' WHERE request_id=%s", (req_id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('admin.housing_requests'))

# -------------------------
# MANAGE UNIVERSITIES
# -------------------------
@admin_bp.route("/admin/universities")
def manage_universities():
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT university_id, name, country, ranking, contact_email
        FROM University
        ORDER BY university_id
    """)
    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin/manage_universities.html", data=data)


@admin_bp.route("/admin/universities/create", methods=["POST"])
def create_university():
    if not guard():
        return redirect(url_for("main.login"))

    name = request.form['name']
    country = request.form['country']
    ranking = request.form['ranking'] or None
    email = request.form['contact_email']

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO University (name, country, ranking, contact_email)
        VALUES (%s, %s, %s, %s)
    """, (name, country, ranking, email))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('admin.manage_universities'))


@admin_bp.route("/admin/universities/delete/<int:uid>")
def delete_university(uid):
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM University WHERE university_id=%s", (uid,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for('admin.manage_universities'))

# -------------------------
# MANAGE MENTORS
# -------------------------
@admin_bp.route("/admin/mentors")
def manage_mentors():
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT m.mentor_id, m.name, m.email, m.department,
               u.name AS university
        FROM Mentor m
        LEFT JOIN University u ON m.university_id = u.university_id
        ORDER BY m.mentor_id
    """)
    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin/manage_mentors.html", data=data)


@admin_bp.route("/admin/mentors/create", methods=["POST"])
def create_mentor():
    if not guard():
        return redirect(url_for("main.login"))

    name = request.form['name']
    email = request.form['email']
    password = generate_password_hash(request.form['password'])
    dept = request.form['department']
    university_id = request.form['university_id'] or None

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO Mentor (name, email, password, department, university_id)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, email, password, dept, university_id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('admin.manage_mentors'))


@admin_bp.route("/admin/mentors/delete/<int:mid>")
def delete_mentor(mid):
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM Mentor WHERE mentor_id=%s", (mid,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for('admin.manage_mentors'))

# ============================================================
# MANAGE PROGRAM REQUIREMENTS
# ============================================================

@admin_bp.route("/admin/requirements/<int:pid>")
def manage_requirements(pid):
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Program info for header
    cur.execute("SELECT title FROM Program WHERE program_id=%s", (pid,))
    program = cur.fetchone()

    # Existing requirements
    cur.execute("""
        SELECT req_id, document_name
        FROM RequiredDocuments
        WHERE program_id=%s
        ORDER BY req_id
    """, (pid,))
    reqs = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "admin/manage_requirements.html",
        program=program,
        pid=pid,
        requirements=reqs
    )


@admin_bp.route("/admin/requirements/<int:pid>/add", methods=["POST"])
def add_requirement(pid):
    if not guard():
        return redirect(url_for("main.login"))

    document_name = request.form["document_name"]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO RequiredDocuments (program_id, document_name)
        VALUES (%s, %s)
    """, (pid, document_name))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("admin.manage_requirements", pid=pid))


@admin_bp.route("/admin/requirements/<int:pid>/delete/<int:req_id>")
def delete_requirement(pid, req_id):
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM RequiredDocuments WHERE req_id=%s", (req_id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for("admin.manage_requirements", pid=pid))

# ----------------------------------
# MANAGE SCHOLARSHIP APPLICATIONS
# ----------------------------------
@admin_bp.route("/admin/scholarship_applications")
def manage_scholarship_applications():
    if not guard():
        return redirect(url_for("main.login"))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        SELECT sa.sch_app_id, sa.status,
               s.name AS student_name,
               p.title AS program_title,
               sc.name AS scholarship_name, sc.amount
        FROM ScholarshipApplication sa
        JOIN Application a ON sa.application_id = a.application_id
        JOIN Student s ON a.student_id = s.student_id
        JOIN Program p ON a.program_id = p.program_id
        JOIN Scholarship sc ON sa.scholarship_id = sc.scholarship_id
        ORDER BY sa.sch_app_id DESC
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("admin/manage_scholarship_applications.html", data=data)

@admin_bp.route("/admin/scholarship_applications/<int:sid>/<string:action>", methods=["POST"])
def decide_scholarship_application(sid, action):
    if not guard():
        return redirect(url_for("main.login"))

    if action not in ("approve", "reject"):
        return redirect(url_for("admin.manage_scholarship_applications"))

    new_status = "Approved" if action == "approve" else "Rejected"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE ScholarshipApplication
        SET status=%s
        WHERE sch_app_id=%s
    """, (new_status, sid))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("admin.manage_scholarship_applications"))
