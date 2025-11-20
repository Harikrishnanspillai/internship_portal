from flask import Blueprint, render_template, session, redirect, url_for, request
from app.db import get_conn
import psycopg2.extras
import os
from werkzeug.utils import secure_filename

student_bp = Blueprint(
    'student',
    __name__,
    template_folder='templates'
)

# -------------------------
# FILE UPLOAD SETTINGS
# -------------------------
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "static", "uploads")
ALLOWED_EXT = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================
# DASHBOARD
# ============================================================
@student_bp.route('/student/dashboard')
def dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    student_id = session['user_id']

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Basic info
    cur.execute("""
        SELECT name, department, cgpa
        FROM Student
        WHERE student_id=%s
    """, (student_id,))
    info = cur.fetchone()

    # Application count
    cur.execute("""
        SELECT COUNT(*) FROM Application WHERE student_id=%s
    """, (student_id,))
    app_count = cur.fetchone()[0]

    # Documents summary
    cur.execute("""
        SELECT 
            COUNT(*) AS total,
            SUM(CASE WHEN ad.status='Approved' THEN 1 ELSE 0 END) AS approved,
            SUM(CASE WHEN ad.status='Rejected' THEN 1 ELSE 0 END) AS rejected,
            SUM(CASE WHEN ad.status='Pending' THEN 1 ELSE 0 END) AS pending
        FROM ApplicationDocument ad
        JOIN Application a ON ad.application_id = a.application_id
        WHERE a.student_id = %s
    """, (student_id,))
    docs = cur.fetchone()


    # Total visa applications
    cur.execute("""
        SELECT COUNT(*) FROM VisaPermit WHERE student_id=%s
    """, (student_id,))
    visa_total = cur.fetchone()[0]

    # Latest visa
    cur.execute("""
        SELECT country, application_status, issued_date, expiry_date
        FROM VisaPermit
        WHERE student_id=%s
        ORDER BY visa_id DESC LIMIT 1
    """, (student_id,))
    visa = cur.fetchone()

    # Housing assignment (latest active)
    cur.execute("""
        SELECT h.location, h.room_type, h.rent,
               ha.allotment_date, ha.checkout_date
        FROM HousingAssignment ha
        JOIN Housing h ON ha.housing_id = h.housing_id
        WHERE ha.student_id=%s
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
        visa_total=visa_total,
        housing=housing
    )


# ============================================================
# PROFILE VIEW + UPDATE
# ============================================================
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
        WHERE student_id=%s
    """, (student_id,))
    data = cur.fetchone()

    cur.close()
    conn.close()

    return render_template('student/profile.html', data=data)


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
        SET name=%s, dob=%s, department=%s, cgpa=%s
        WHERE student_id=%s
    """, (name, dob, dept, cgpa, student_id))
    conn.commit()

    cur.close()
    conn.close()
    return redirect(url_for('student.profile'))


# ============================================================
# VIEW PROGRAMS
# ============================================================
@student_bp.route('/student/programs')
def programs():
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("""
        SELECT p.program_id, p.title, u.name AS university,
               m.name AS mentor, p.duration
        FROM Program p
        LEFT JOIN University u ON p.university_id=u.university_id
        LEFT JOIN Mentor m ON p.mentor_id=m.mentor_id
        ORDER BY p.program_id
    """)
    programs = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('student/view_programs.html', programs=programs)


@student_bp.route('/student/program/<int:pid>')
def program_details(pid):
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    student_id = session['user_id']
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # load program info
    cur.execute("""
        SELECT p.*, u.name AS university, m.name AS mentor
        FROM Program p
        LEFT JOIN University u ON p.university_id=u.university_id
        LEFT JOIN Mentor m ON p.mentor_id=m.mentor_id
        WHERE p.program_id=%s
    """, (pid,))
    program = cur.fetchone()

    # check application
    cur.execute("""
        SELECT application_id FROM Application 
        WHERE student_id=%s AND program_id=%s
    """, (student_id, pid))
    app = cur.fetchone()

    applied = bool(app)
    app_id = app["application_id"] if applied else None

    requirements = []
    documents = {}

    if applied:
        # load requirements
        cur.execute("""
            SELECT req_id, document_name
            FROM RequiredDocuments
            WHERE program_id=%s
        """, (pid,))
        requirements = cur.fetchall()

        # load uploaded documents
        cur.execute("""
            SELECT req_id, file_name, status
            FROM ApplicationDocument
            WHERE application_id=%s
        """, (app_id,))
        for row in cur.fetchall():
            documents[row["req_id"]] = row

    # scholarships
    cur.execute("""
        SELECT scholarship_id, name, amount, eligibility_criteria
        FROM Scholarship
        WHERE program_id=%s
    """, (pid,))
    scholarships = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "student/program_details.html",
        program=program,
        pid=pid,
        applied=applied,
        app_id=app_id,
        requirements=requirements,
        documents=documents,
        scholarships=scholarships
    )

@student_bp.route('/student/program/<int:pid>/apply')
def apply(pid):
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    student_id = session['user_id']

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # check if already applied
    cur.execute("""
        SELECT application_id
        FROM Application
        WHERE student_id=%s AND program_id=%s
    """, (student_id, pid))
    exists = cur.fetchone()

    # create application if missing
    if not exists:
        cur.execute("""
            INSERT INTO Application (student_id, program_id)
            VALUES (%s, %s)
        """, (student_id, pid))
        conn.commit()

    cur.close()
    conn.close()

    return redirect(url_for('student.program_details', pid=pid))



# ============================================================
# DOCUMENT UPLOADS
# ============================================================

@student_bp.route('/student/program/<int:pid>/upload/<int:app_id>/<int:req_id>', methods=['POST'])
def upload_required_doc(pid, app_id, req_id):
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    f = request.files.get("file")
    if not f:
        return redirect(url_for('student.program_details', pid=pid))

    filename = secure_filename(f.filename)
    ext = filename.rsplit('.',1)[-1].lower()

    if ext not in ALLOWED_EXT:
        return redirect(url_for('student.program_details', pid=pid))

    dest = os.path.join(UPLOAD_FOLDER, filename)
    f.save(dest)

    conn = get_conn()
    cur = conn.cursor()

    # either insert new or overwrite
    cur.execute("""
        INSERT INTO ApplicationDocument (application_id, req_id, file_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (application_id, req_id)
        DO UPDATE SET file_name = EXCLUDED.file_name,
                      status = 'Pending'
    """, (app_id, req_id, filename))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('student.program_details', pid=pid))

# ============================================================
# VISA APPLICATIONS
# ============================================================
@student_bp.route('/student/visa', methods=['GET', 'POST'])
def visa_applications():
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    student_id = session['user_id']

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # fetch valid visa countries from programs offered
    cur.execute("""
        SELECT DISTINCT u.country
        FROM Program p
        JOIN University u ON p.university_id = u.university_id
        ORDER BY u.country
    """)
    valid_countries = [row["country"] for row in cur.fetchall()]

    if request.method == 'POST':
        country = request.form.get('country')

        if country not in valid_countries:
            cur.close()
            conn.close()
            return render_template('student/visa.html',
                                   error="Invalid country selection.",
                                   visas=[],
                                   valid_countries=valid_countries)

        cur.execute("""
            INSERT INTO VisaPermit (student_id, country)
            VALUES (%s, %s)
        """, (student_id, country))
        conn.commit()

    # fetch student visa history
    cur.execute("""
        SELECT visa_id, country, application_status, issued_date, expiry_date
        FROM VisaPermit
        WHERE student_id = %s
        ORDER BY visa_id DESC
    """, (student_id,))
    visas = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'student/visa.html',
        visas=visas,
        valid_countries=valid_countries
    )



# ============================================================
# HOUSING (Student Requests + View Assignment)
# ============================================================
@student_bp.route('/student/housing', methods=['GET', 'POST'])
def housing():
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    student_id = session['user_id']

    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Current active housing (if any)
    cur.execute("""
        SELECT h.location, h.room_type, h.rent,
               ha.allotment_date, ha.checkout_date
        FROM HousingAssignment ha
        JOIN Housing h ON ha.housing_id=h.housing_id
        WHERE ha.student_id=%s AND ha.checkout_date IS NULL
        ORDER BY ha.assign_id DESC LIMIT 1
    """, (student_id,))
    current = cur.fetchone()

    # Student's request history
    cur.execute("""
        SELECT request_id, request_type, status, request_date
        FROM HousingRequest
        WHERE student_id=%s
        ORDER BY request_date DESC
    """, (student_id,))
    requests = cur.fetchall()

    if request.method == 'POST':
        action = request.form.get('action')

        if action not in ("apply", "vacate"):
            return render_template("student/housing.html",
                                   current=current, requests=requests,
                                   error="Invalid action.")

        if action == "apply" and current:
            return render_template("student/housing.html",
                                   current=current, requests=requests,
                                   error="You already have housing.")

        if action == "vacate" and not current:
            return render_template("student/housing.html",
                                   current=current, requests=requests,
                                   error="You have no housing to vacate.")

        cur.execute("""
            INSERT INTO HousingRequest (student_id, request_type)
            VALUES (%s, %s)
        """, (student_id, action))
        conn.commit()

        cur.execute("""
            SELECT request_id, request_type, status, request_date
            FROM HousingRequest
            WHERE student_id=%s
            ORDER BY request_date DESC
        """, (student_id,))
        requests = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("student/housing.html",
                           current=current,
                           requests=requests)

@student_bp.route('/student/scholarship/apply/<int:app_id>/<int:sid>', methods=['POST'])
def apply_scholarship(app_id, sid):
    if session.get('role') != 'student':
        return redirect(url_for('main.login'))

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO ScholarshipApplication (application_id, scholarship_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (app_id, sid))

    conn.commit()
    cur.close()
    conn.close()

    # must redirect using program_id
    return redirect(request.referrer)
