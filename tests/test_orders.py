def _pedido(staff_client, menu):
    return staff_client.post("/api/orders", json={"items": [
        {"dish_id": menu["bandeja"], "quantity": 2},
        {"dish_id": menu["sopa"], "quantity": 1},
    ]})


def test_total_se_calcula_con_precios_de_la_base(staff, menu):
    resp = _pedido(staff["cliente"], menu)
    assert resp.status_code == 201
    assert resp.get_json()["total"] == 62000


def test_plato_no_disponible_se_rechaza(staff, menu):
    staff["admin"].put(f"/api/dishes/{menu['sopa']}", json={"available": False})
    resp = _pedido(staff["cliente"], menu)
    assert resp.status_code == 400


def test_cliente_solo_ve_sus_pedidos(app, staff, menu, login_as):
    _pedido(staff["cliente"], menu)
    otro = login_as("cliente2", "cliente")
    _pedido(otro, menu)
    assert len(staff["cliente"].get("/api/orders").get_json()) == 1
    assert len(staff["mesero"].get("/api/orders").get_json()) == 2


def test_flujo_completo_de_estados(staff, menu):
    pedido = _pedido(staff["cliente"], menu).get_json()
    url = f"/api/orders/{pedido['id']}/status"
    for estado in ("en_preparacion", "listo", "entregado"):
        resp = staff["mesero"].patch(url, json={"status": estado})
        assert resp.status_code == 200
        assert resp.get_json()["status"] == estado


def test_transicion_invalida_devuelve_400(staff, menu):
    pedido = _pedido(staff["cliente"], menu).get_json()
    resp = staff["mesero"].patch(f"/api/orders/{pedido['id']}/status", json={"status": "entregado"})
    assert resp.status_code == 400


def test_cliente_no_puede_cambiar_estado(staff, menu):
    pedido = _pedido(staff["cliente"], menu).get_json()
    resp = staff["cliente"].patch(f"/api/orders/{pedido['id']}/status", json={"status": "en_preparacion"})
    assert resp.status_code == 403
