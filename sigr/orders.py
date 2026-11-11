"""Módulo de pedidos: registro y seguimiento del estado."""
from datetime import datetime

from flask import Blueprint, jsonify, request

from .auth import require_roles
from .db import get_db

bp = Blueprint("orders", __name__, url_prefix="/api")

TRANSITIONS = {
    "recibido": {"en_preparacion", "cancelado"},
    "en_preparacion": {"listo", "cancelado"},
    "listo": {"entregado"},
    "entregado": set(),
    "cancelado": set(),
}


def _serialize(db, row):
    items = db.execute(
        """SELECT oi.dish_id, d.name, oi.quantity, oi.unit_price
           FROM order_items oi JOIN dishes d ON d.id = oi.dish_id
           WHERE oi.order_id = ?""",
        (row["id"],),
    ).fetchall()
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "status": row["status"],
        "total": row["total"],
        "created_at": row["created_at"],
        "items": [dict(i) for i in items],
    }


@bp.post("/orders")
@require_roles("cliente", "mesero")
def create_order(user):
    items = (request.get_json(silent=True) or {}).get("items")
    if not isinstance(items, list) or not items:
        return jsonify(error="El pedido debe tener al menos un plato"), 400

    db = get_db()
    total = 0.0
    lines = []
    for item in items:
        dish_id = item.get("dish_id") if isinstance(item, dict) else None
        quantity = item.get("quantity") if isinstance(item, dict) else None
        if not isinstance(dish_id, int) or not isinstance(quantity, int) or quantity <= 0:
            return jsonify(error="Cada ítem necesita dish_id y quantity > 0"), 400
        dish = db.execute("SELECT id, price, available FROM dishes WHERE id = ?", (dish_id,)).fetchone()
        if dish is None or not dish["available"]:
            return jsonify(error=f"El plato {dish_id} no está disponible"), 400
        total += dish["price"] * quantity
        lines.append((dish_id, quantity, dish["price"]))

    created_at = datetime.now().isoformat(timespec="seconds")
    cur = db.execute(
        "INSERT INTO orders (user_id, status, total, created_at) VALUES (?, 'recibido', ?, ?)",
        (user["id"], round(total, 2), created_at),
    )
    order_id = cur.lastrowid
    db.executemany(
        "INSERT INTO order_items (order_id, dish_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
        [(order_id, d, q, p) for d, q, p in lines],
    )
    db.commit()
    row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return jsonify(_serialize(db, row)), 201


@bp.get("/orders")
@require_roles()
def list_orders(user):
    db = get_db()
    if user["role"] == "cliente":
        rows = db.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id", (user["id"],)).fetchall()
    else:
        rows = db.execute("SELECT * FROM orders ORDER BY id").fetchall()
    return jsonify([_serialize(db, r) for r in rows])


@bp.patch("/orders/<int:order_id>/status")
@require_roles("mesero", "administrador")
def update_status(_user, order_id):
    new_status = (request.get_json(silent=True) or {}).get("status")
    db = get_db()
    row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if row is None:
        return jsonify(error="Pedido no encontrado"), 404
    if new_status not in TRANSITIONS.get(row["status"], set()):
        return jsonify(error=f"No se puede pasar de '{row['status']}' a '{new_status}'"), 400
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    db.commit()
    row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return jsonify(_serialize(db, row))
