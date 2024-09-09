from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, 
                template_folder=os.path.abspath('templates'),
                static_folder=os.path.abspath('static'))
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        from app import models  # Import models here
        db.create_all()  # This will create all tables, including the new UploadHistory table

    for folder in [app.config['UPLOAD_FOLDER'], app.config['HISTORY_FOLDER']]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    from app import routes
    app.register_blueprint(routes.main)

    return app