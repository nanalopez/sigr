from datetime import date, timedelta

FUTURO = (date.today() + timedelta(days=3)).isoformat()


def test_reserva_valida(staff):
    resp = staff["cliente"].post("/api/reservations", json={"date": FUTURO, "time": "19:30", "people": 4})
    assert resp.status_code == 201
    assert resp.get_json()["status"] == "activa"


def test_formato_de_hora_invalido(staff):
    resp = staff["cliente"].post("/api/reservations", json={"date": FUTURO, "time": "7pm", "people": 2})
    assert resp.status_code == 400


def test_fecha_pasada_se_rechaza(staff):
    ayer = (date.today() - timedelta(days=1)).isoformat()
    resp = staff["cliente"].post("/api/reservations", json={"date": ayer, "time": "12:00", "people": 2})
    assert resp.status_code == 400


def test_limite_por_horario(staff, login_as):
    body = {"date": FUTURO, "time": "20:00", "people": 2}
    assert staff["cliente"].post("/api/reservations", json=body).status_code == 201
    assert login_as("cliente2", "cliente").post("/api/reservations", json=body).status_code == 201
    assert login_as("cliente3", "cliente").post("/api/reservations", json=body).status_code == 409


def test_cancelar_propia_reserva(staff):
    res = staff["cliente"].post("/api/reservations", json={"date": FUTURO, "time": "13:00", "people": 3}).get_json()
    resp = staff["cliente"].delete(f"/api/reservations/{res['id']}")
    assert resp.status_code == 200
    assert staff["cliente"].get("/api/reservations").get_json()[0]["status"] == "cancelada"
