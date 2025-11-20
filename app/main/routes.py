from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2 import IntegrityError
from app.db import get_conn

main_bp = Blueprint('main', __name__, template_folder='templates')

@main_bp.route('/')
def index():
    return render_template('main/index.html')

@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        
        if not name or not email or not password:
            return render_template('main/signup.html', error="All fields are required.", form=request.form)

        if password != confirm:
            return render_template('main/signup.html', error="Passwords do not match.", form=request.form)

        pw_hash = generate_password_hash(password)  

        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO Student (name, email, password)
                VALUES (%s, %s, %s)
                """,
                (name, email, pw_hash)
            )
            conn.commit()
        except IntegrityError:
            conn.rollback()
            cur.close()
            conn.close()
            return render_template('main/signup.html', error="An account with that email already exists.", form=request.form)
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            return render_template('main/signup.html', error="Unexpected error: " + str(e), form=request.form)

        cur.close()
        conn.close()

        
        return redirect(url_for('main.login'))

    return render_template('main/signup.html')


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            return render_template('main/login.html', error="Email and password required.", form=request.form)

        conn = get_conn()
        cur = conn.cursor()

        
        cur.execute("SELECT student_id, name, password FROM Student WHERE email = %s", (email,))
        user = cur.fetchone()
        if user:
            user_id, name, pw_hash = user
            if check_password_hash(pw_hash, password):
                session.clear()
                session['user_id'] = user_id
                session['role'] = 'student'
                session['name'] = name
                cur.close()
                conn.close()
                return redirect(url_for('student.dashboard'))
            else:
                cur.close()
                conn.close()
                return render_template('main/login.html', error="Invalid credentials.", form=request.form)

        
        cur.execute("SELECT mentor_id, name, password FROM Mentor WHERE email = %s", (email,))
        m = cur.fetchone()
        if m:
            mentor_id, name, pw_hash = m
            if check_password_hash(pw_hash, password):
                session.clear()
                session['user_id'] = mentor_id
                session['role'] = 'mentor'
                session['name'] = name
                cur.close()
                conn.close()
                return redirect(url_for('mentor.dashboard'))
            else:
                cur.close()
                conn.close()
                return render_template('main/login.html', error="Invalid credentials.", form=request.form)

        
        cur.execute("SELECT admin_id, name, password FROM Admin WHERE email = %s", (email,))
        a = cur.fetchone()
        cur.close()
        conn.close()
        if a:
            admin_id, name, pw_hash = a
            if check_password_hash(pw_hash, password):
                session.clear()
                session['user_id'] = admin_id
                session['role'] = 'admin'
                session['name'] = name
                return redirect(url_for('admin.dashboard'))
            else:
                return render_template('main/login.html', error="Invalid credentials.", form=request.form)

        
        return render_template('main/login.html', error="No account with that email.", form=request.form)

    return render_template('main/login.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))