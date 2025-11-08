from flask import Blueprint, render_template

student_bp = Blueprint('student', __name__, template_folder='templates')

@student_bp.route('/student/dashboard')
def dashboard():
    return render_template('student/dashboard.html')