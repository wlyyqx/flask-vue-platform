from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import db, jwt


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    jwt.init_app(app)

    from .api import register_blueprints
    register_blueprints(app)

    with app.app_context():
        from . import models  # noqa
        db.create_all()

    @app.get("/")
    def index():
        return {"message": "Test Platform API is running"}

    return app