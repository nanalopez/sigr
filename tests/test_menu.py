def test_cualquiera_puede_ver_el_menu(client, menu):
    resp = client.get("/api/dishes")
    assert resp.status_code == 200
    assert {d["name"] for d in resp.get_json()} == {"Bandeja", "Sopa"}


def test_precio_negativo_devuelve_400(staff, menu):
    resp = staff["admin"].post("/api/dishes", json={"category_id": menu["categoria"], "name": "X", "price": -1})
    assert resp.status_code == 400


def test_actualizar_disponibilidad(staff, menu):
    resp = staff["admin"].put(f"/api/dishes/{menu['sopa']}", json={"available": False})
    assert resp.status_code == 200
    assert resp.get_json()["available"] == 0


def test_eliminar_plato_sin_pedidos(staff, menu):
    resp = staff["admin"].delete(f"/api/dishes/{menu['sopa']}")
    assert resp.status_code == 200
