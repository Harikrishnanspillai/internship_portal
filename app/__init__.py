from flask import Flask

from app.main.routes import main_bp
from app.student.routes import student_bp
from app.mentor.routes import mentor_bp
from app.admin.routes import admin_bp

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.register_blueprint(main_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(mentor_bp)
    app.register_blueprint(admin_bp)
    return app