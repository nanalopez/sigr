"""Módulo de cierre de caja y reportes de ventas diarios."""
import sqlite3
from datetime import date, datetime

from flask import Blueprint, jsonify, request

from .auth import require_roles
from .db import get_db

bp = Blueprint("cashier", __name__, url_prefix="/api")


def _day_param():
    value = request.args.get("date") or date.today().isoformat()
    datetime.strptime(value, "%Y-%m-%d")  # lanza ValueError si el formato no es válido
    return value


@bp.get("/reports/daily")
@require_roles("administrador")
def daily_report(_user):
    try:
        day = _day_param()
    except ValueError:
        return jsonify(error="Fecha no válida (AAAA-MM-DD)"), 400
    db = get_db()
    counts = db.execute(
        "SELECT status, COUNT(*) AS n FROM orders WHERE substr(created_at, 1, 10) = ? GROUP BY status",
        (day,),
    ).fetchall()
    sales = db.execute(
        """SELECT COALESCE(SUM(total), 0) AS total, COUNT(*) AS n FROM orders
           WHERE substr(created_at, 1, 10) = ? AND status = 'entregado'""",
        (day,),
    ).fetchone()
    return jsonify(
        date=day,
        total_sales=round(sales["total"], 2),
        delivered_orders=sales["n"],
        orders_by_status={r["status"]: r["n"] for r in counts},
    )


@bp.post("/cash-closings")
@require_roles("administrador")
def close_cash(user):
    data = request.get_json(silent=True) or {}
    day = data.get("date") or date.today().isoformat()
    try:
        datetime.strptime(str(day), "%Y-%m-%d")
    except ValueError:
        return jsonify(error="Fecha no válida (AAAA-MM-DD)"), 400

    db = get_db()
    totals = db.execute(
        """SELECT COALESCE(SUM(total), 0) AS total, COUNT(*) AS n FROM orders
           WHERE substr(created_at, 1, 10) = ? AND status = 'entregado'""",
        (day,),
    ).fetchone()
    try:
        cur = db.execute(
            """INSERT INTO cash_closings (date, total_sales, orders_count, closed_by, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (day, round(totals["total"], 2), totals["n"], user["id"],
             datetime.now().isoformat(timespec="seconds")),
        )
    except sqlite3.IntegrityError:
        return jsonify(error="Ese día ya tiene un cierre de caja"), 409
    db.commit()
    return jsonify(id=cur.lastrowid, date=day, total_sales=round(totals["total"], 2),
                   orders_count=totals["n"]), 201


@bp.get("/cash-closings")
@require_roles("administrador")
def list_closings(_user):
    rows = get_db().execute("SELECT * FROM cash_closings ORDER BY date DESC").fetchall()
    return jsonify([dict(r) for r in rows])
