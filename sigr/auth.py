"""Usuarios, inicio de sesión y control de roles."""
import functools
import os
import sqlite3

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/api")
ROLES = ("cliente", "mesero", "administrador")


def create_user(username, password, role):
    db = get_db()
    db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, generate_password_hash(password), role),
    )
    db.commit()


def current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return get_db().execute(
        "SELECT id, username, role FROM users WHERE id = ?", (user_id,)
    ).fetchone()


def require_roles(*roles):
    """Decorador: exige sesión iniciada y, si se indican, uno de los roles."""

    def decorator(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                return jsonify(error="Debe iniciar sesión"), 401
            if roles and user["role"] not in roles:
                return jsonify(error="No autorizado para esta acción"), 403
            return view(user, *args, **kwargs)

        return wrapped

    return decorator


def ensure_admin(app):
    """Crea el administrador inicial si las variables de entorno están definidas."""
    username = os.environ.get("SIGR_ADMIN_USER")
    password = os.environ.get("SIGR_ADMIN_PASSWORD")
    if not username or not password:
        return
    with app.app_context():
        exists = get_db().execute(
            "SELECT 1 FROM users WHERE role = 'administrador' LIMIT 1"
        ).fetchone()
        if not exists:
            create_user(username, password, "administrador")


def _credentials():
    data = request.get_json(silent=True) or {}
    return str(data.get("username", "")).strip(), str(data.get("password", ""))


@bp.post("/auth/register")
def register():
    username, password = _credentials()
    if len(username) < 3:
        return jsonify(error="El usuario debe tener al menos 3 caracteres"), 400
    if len(password) < 6:
        return jsonify(error="La contraseña debe tener al menos 6 caracteres"), 400
    try:
        create_user(username, password, "cliente")
    except sqlite3.IntegrityError:
        return jsonify(error="El usuario ya existe"), 409
    return jsonify(message="Usuario creado"), 201


@bp.post("/auth/login")
def login():
    username, password = _credentials()
    user = get_db().execute(
        "SELECT id, username, password_hash, role FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify(error="Usuario o contraseña incorrectos"), 401
    session.clear()
    session["user_id"] = user["id"]
    return jsonify(id=user["id"], username=user["username"], role=user["role"])


@bp.post("/auth/logout")
def logout():
    session.clear()
    return jsonify(message="Sesión cerrada")


@bp.get("/auth/me")
@require_roles()
def me(user):
    return jsonify(id=user["id"], username=user["username"], role=user["role"])


@bp.post("/users")
@require_roles("administrador")
def create_staff(_user):
    username, password = _credentials()
    role = (request.get_json(silent=True) or {}).get("role", "mesero")
    if role not in ROLES:
        return jsonify(error="Rol no válido"), 400
    if len(username) < 3 or len(password) < 6:
        return jsonify(error="Usuario o contraseña no válidos"), 400
    try:
        create_user(username, password, role)
    except sqlite3.IntegrityError:
        return jsonify(error="El usuario ya existe"), 409
    return jsonify(message="Usuario creado", role=role), 201
