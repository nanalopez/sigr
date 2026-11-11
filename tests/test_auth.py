def test_registro_de_cliente(client):
    resp = client.post("/api/auth/register", json={"username": "ana", "password": "secreto123"})
    assert resp.status_code == 201


def test_usuario_duplicado_devuelve_409(client):
    client.post("/api/auth/register", json={"username": "ana", "password": "secreto123"})
    resp = client.post("/api/auth/register", json={"username": "ana", "password": "secreto123"})
    assert resp.status_code == 409


def test_contrasena_corta_devuelve_400(client):
    resp = client.post("/api/auth/register", json={"username": "ana", "password": "123"})
    assert resp.status_code == 400


def test_login_con_contrasena_incorrecta_devuelve_401(client):
    client.post("/api/auth/register", json={"username": "ana", "password": "secreto123"})
    resp = client.post("/api/auth/login", json={"username": "ana", "password": "otra"})
    assert resp.status_code == 401


def test_me_sin_sesion_devuelve_401(client):
    assert client.get("/api/auth/me").status_code == 401


def test_cliente_no_puede_crear_categorias(staff):
    resp = staff["cliente"].post("/api/categories", json={"name": "Bebidas"})
    assert resp.status_code == 403


def test_admin_crea_personal(staff):
    resp = staff["admin"].post("/api/users", json={"username": "nuevo", "password": "secreto123", "role": "mesero"})
    assert resp.status_code == 201
