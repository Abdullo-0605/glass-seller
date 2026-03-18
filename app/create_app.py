"""Flask application factory."""
import os
from flask import Flask, g
from .models import db
from .routes import main, admin
from .auth import auth, load_user


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(os.path.dirname(__file__), "..", "instance", "glass_seller.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit

    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "instance"), exist_ok=True)

    db.init_app(app)
    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(auth)

    @app.before_request
    def _load_user():
        load_user()

    @app.context_processor
    def inject_user():
        return dict(current_user=g.get("user"))

    with app.app_context():
        db.create_all()

    return app
