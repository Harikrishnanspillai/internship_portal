from flask import Blueprint, render_template, redirect, url_for

main_bp = Blueprint('main', __name__, template_folder='templates')

@main_bp.route('/')
def index():
    return render_template('main/index.html')

@main_bp.route('/login')
def login():
    return render_template('main/login.html')

@main_bp.route('/signup')
def signup():
    return render_template('main/signup.html')
