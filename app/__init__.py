from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate

from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*") #this is just for develpment we wont allow cors from any where in prod ofc.
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)

    from app.routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    @app.errorhandler(404)
    def not_found_error(error):
        return "404 Not Found", 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return "500 Internal Server Error", 500
    
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')

    return app