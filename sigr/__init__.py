"""Sistema Integral de Gestión de Restaurante (SIGR)."""
import os

from flask import Flask, send_from_directory

from .auth import bp as auth_bp, ensure_admin
from .cashier import bp as cashier_bp
from .db import init_app
from .menu import bp as menu_bp
from .orders import bp as orders_bp
from .reservations import bp as reservations_bp


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.update(
        SECRET_KEY=os.environ.get("SIGR_SECRET_KEY", "cambiar-en-produccion"),
        DATABASE=os.environ.get("SIGR_DB", os.path.join("instance", "sigr.db")),
        MAX_RESERVATIONS_PER_SLOT=int(os.environ.get("SIGR_MAX_RESERVAS", "5")),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(os.path.dirname(os.path.abspath(app.config["DATABASE"])), exist_ok=True)
    init_app(app)
    ensure_admin(app)

    for blueprint in (auth_bp, menu_bp, orders_bp, reservations_bp, cashier_bp):
        app.register_blueprint(blueprint)

    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    return app
