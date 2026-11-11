"""Módulo de menú digital: CRUD de categorías y platos."""
import sqlite3

from flask import Blueprint, jsonify, request

from .auth import require_roles
from .db import get_db

bp = Blueprint("menu", __name__, url_prefix="/api")


def _valid_price(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


@bp.get("/categories")
def list_categories():
    rows = get_db().execute("SELECT id, name FROM categories ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/categories")
@require_roles("administrador")
def create_category(_user):
    name = str((request.get_json(silent=True) or {}).get("name", "")).strip()
    if not name:
        return jsonify(error="El nombre es obligatorio"), 400
    db = get_db()
    try:
        cur = db.execute("INSERT INTO categories (name) VALUES (?)", (name,))
    except sqlite3.IntegrityError:
        return jsonify(error="La categoría ya existe"), 409
    db.commit()
    return jsonify(id=cur.lastrowid, name=name), 201


@bp.get("/dishes")
def list_dishes():
    rows = get_db().execute(
        """SELECT d.id, d.name, d.price, d.available, d.category_id, c.name AS category
           FROM dishes d JOIN categories c ON c.id = d.category_id
           ORDER BY c.name, d.name"""
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/dishes")
@require_roles("administrador")
def create_dish(_user):
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not name or not _valid_price(data.get("price")):
        return jsonify(error="Nombre y precio (>= 0) son obligatorios"), 400
    db = get_db()
    if db.execute("SELECT 1 FROM categories WHERE id = ?", (data.get("category_id"),)).fetchone() is None:
        return jsonify(error="La categoría no existe"), 400
    cur = db.execute(
        "INSERT INTO dishes (category_id, name, price) VALUES (?, ?, ?)",
        (data["category_id"], name, data["price"]),
    )
    db.commit()
    return jsonify(id=cur.lastrowid, name=name, price=data["price"]), 201


@bp.put("/dishes/<int:dish_id>")
@require_roles("administrador")
def update_dish(_user, dish_id):
    data = request.get_json(silent=True) or {}
    db = get_db()
    dish = db.execute("SELECT * FROM dishes WHERE id = ?", (dish_id,)).fetchone()
    if dish is None:
        return jsonify(error="Plato no encontrado"), 404
    name = str(data.get("name", dish["name"])).strip()
    price = data.get("price", dish["price"])
    available = int(bool(data.get("available", dish["available"])))
    if not name or not _valid_price(price):
        return jsonify(error="Nombre o precio no válidos"), 400
    db.execute(
        "UPDATE dishes SET name = ?, price = ?, available = ? WHERE id = ?",
        (name, price, available, dish_id),
    )
    db.commit()
    return jsonify(id=dish_id, name=name, price=price, available=available)


@bp.delete("/dishes/<int:dish_id>")
@require_roles("administrador")
def delete_dish(_user, dish_id):
    db = get_db()
    used = db.execute("SELECT 1 FROM order_items WHERE dish_id = ? LIMIT 1", (dish_id,)).fetchone()
    if used:
        return jsonify(error="El plato tiene pedidos; márquelo como no disponible"), 409
    cur = db.execute("DELETE FROM dishes WHERE id = ?", (dish_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify(error="Plato no encontrado"), 404
    return jsonify(message="Plato eliminado")
