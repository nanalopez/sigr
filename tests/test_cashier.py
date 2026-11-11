from datetime import date


def _entregar(staff, menu, cantidad):
    pedido = staff["cliente"].post("/api/orders", json={"items": [
        {"dish_id": menu["bandeja"], "quantity": cantidad}]}).get_json()
    url = f"/api/orders/{pedido['id']}/status"
    for estado in ("en_preparacion", "listo", "entregado"):
        staff["mesero"].patch(url, json={"status": estado})
    return pedido


def test_cierre_suma_solo_pedidos_entregados(staff, menu):
    _entregar(staff, menu, 2)  # 50.000
    pendiente = staff["cliente"].post("/api/orders", json={"items": [
        {"dish_id": menu["sopa"], "quantity": 1}]}).get_json()
    assert pendiente["status"] == "recibido"

    resp = staff["admin"].post("/api/cash-closings", json={"date": date.today().isoformat()})
    assert resp.status_code == 201
    assert resp.get_json()["total_sales"] == 50000
    assert resp.get_json()["orders_count"] == 1


def test_cierre_duplicado_devuelve_409(staff, menu):
    hoy = date.today().isoformat()
    staff["admin"].post("/api/cash-closings", json={"date": hoy})
    assert staff["admin"].post("/api/cash-closings", json={"date": hoy}).status_code == 409


def test_solo_admin_cierra_caja(staff):
    assert staff["mesero"].post("/api/cash-closings", json={}).status_code == 403


def test_reporte_diario_por_estado(staff, menu):
    _entregar(staff, menu, 1)
    resp = staff["admin"].get(f"/api/reports/daily?date={date.today().isoformat()}")
    datos = resp.get_json()
    assert resp.status_code == 200
    assert datos["total_sales"] == 25000
    assert datos["orders_by_status"]["entregado"] == 1


def test_fecha_invalida_en_reporte(staff):
    assert staff["admin"].get("/api/reports/daily?date=31-12-2026").status_code == 400
