from flask import Blueprint, render_template

mentor_bp = Blueprint('mentor', __name__, template_folder='templates')

@mentor_bp.route('/mentor/dashboard')
def dashboard():
    return render_template('mentor/dashboard.html')