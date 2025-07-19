
from flask import Flask
from sqlalchemy import text

from app.extensions import db, limiter, login_manager
from app.utils import configure_relationships, delete_table
from config import settings, prepare_folders
from app.cli import register_commands

def create_app(migrate=False, drop_all=False):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_mapping(
        SECRET_KEY=settings.SECRET_KEY,
        DEBUG=settings.DEBUG,
        TESTING=settings.TESTING,
        SQLALCHEMY_DATABASE_URI=settings.db.SQLALCHEMY_DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=settings.db.SQLALCHEMY_TRACK_MODIFICATIONS,
        UPLOAD_FOLDER=str(settings.db.UPLOAD_FOLDER),
    )

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    # limiter.init_app(app)

    from app.collection import collection_bp
    from app.user import user_bp
    from app.main import main_bp
    from app.api import api_bp
    from app.jwt import jwt_bp
    from app.nft import nft_bp

    app.register_blueprint(collection_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(jwt_bp)
    app.register_blueprint(nft_bp)

    configure_relationships()

    register_commands(app)

    if migrate:
        prepare_folders()

        with app.app_context():
            if drop_all:
                db.drop_all()
            db.create_all()
    return app
