"""Módulo de reservas por fecha y hora."""
from datetime import date, datetime

from flask import Blueprint, current_app, jsonify, request

from .auth import require_roles
from .db import get_db

bp = Blueprint("reservations", __name__, url_prefix="/api")
STAFF = ("mesero", "administrador")


def _parse(data):
    try:
        day = datetime.strptime(str(data.get("date", "")), "%Y-%m-%d").date()
        time = datetime.strptime(str(data.get("time", "")), "%H:%M").strftime("%H:%M")
    except ValueError:
        return None, None, "Fecha (AAAA-MM-DD) u hora (HH:MM) no válidas"
    people = data.get("people")
    if not isinstance(people, int) or isinstance(people, bool) or not 1 <= people <= 20:
        return None, None, "El número de personas debe estar entre 1 y 20"
    if day < date.today():
        return None, None, "No se pueden reservar fechas pasadas"
    return day.isoformat(), time, None


@bp.post("/reservations")
@require_roles("cliente", "mesero", "administrador")
def create_reservation(user):
    data = request.get_json(silent=True) or {}
    day, time, error = _parse(data)
    if error:
        return jsonify(error=error), 400

    db = get_db()
    taken = db.execute(
        "SELECT COUNT(*) FROM reservations WHERE date = ? AND time = ? AND status = 'activa'",
        (day, time),
    ).fetchone()[0]
    if taken >= current_app.config["MAX_RESERVATIONS_PER_SLOT"]:
        return jsonify(error="Ese horario ya no tiene disponibilidad"), 409

    cur = db.execute(
        "INSERT INTO reservations (user_id, date, time, people, status) VALUES (?, ?, ?, ?, 'activa')",
        (user["id"], day, time, data["people"]),
    )
    db.commit()
    return jsonify(id=cur.lastrowid, date=day, time=time, people=data["people"], status="activa"), 201


@bp.get("/reservations")
@require_roles()
def list_reservations(user):
    db = get_db()
    query = "SELECT id, user_id, date, time, people, status FROM reservations"
    params = []
    clauses = []
    if user["role"] not in STAFF:
        clauses.append("user_id = ?")
        params.append(user["id"])
    if request.args.get("date"):
        clauses.append("date = ?")
        params.append(request.args["date"])
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY date, time"
    return jsonify([dict(r) for r in db.execute(query, params).fetchall()])


@bp.delete("/reservations/<int:res_id>")
@require_roles()
def cancel_reservation(user, res_id):
    db = get_db()
    row = db.execute("SELECT user_id, status FROM reservations WHERE id = ?", (res_id,)).fetchone()
    if row is None:
        return jsonify(error="Reserva no encontrada"), 404
    if row["user_id"] != user["id"] and user["role"] not in STAFF:
        return jsonify(error="No autorizado para cancelar esta reserva"), 403
    if row["status"] == "cancelada":
        return jsonify(error="La reserva ya está cancelada"), 409
    db.execute("UPDATE reservations SET status = 'cancelada' WHERE id = ?", (res_id,))
    db.commit()
    return jsonify(message="Reserva cancelada")
