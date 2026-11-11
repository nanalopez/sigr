import pytest

from sigr import create_app
from sigr.auth import create_user


@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
        "SECRET_KEY": "test",
        "MAX_RESERVATIONS_PER_SLOT": 2,
    })


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login_as(app):
    """Crea un usuario con el rol indicado y devuelve un cliente con sesión iniciada."""

    def _login(username, role, password="secreto123"):
        with app.app_context():
            create_user(username, password, role)
        c = app.test_client()
        resp = c.post("/api/auth/login", json={"username": username, "password": password})
        assert resp.status_code == 200, resp.get_json()
        return c

    return _login


@pytest.fixture
def staff(login_as):
    return {
        "admin": login_as("admin", "administrador"),
        "mesero": login_as("mesero1", "mesero"),
        "cliente": login_as("cliente1", "cliente"),
    }


@pytest.fixture
def menu(staff):
    """Crea una categoría y dos platos disponibles; devuelve sus ids."""
    admin = staff["admin"]
    cat = admin.post("/api/categories", json={"name": "Fuertes"}).get_json()["id"]
    plato_a = admin.post("/api/dishes", json={"category_id": cat, "name": "Bandeja", "price": 25000}).get_json()["id"]
    plato_b = admin.post("/api/dishes", json={"category_id": cat, "name": "Sopa", "price": 12000}).get_json()["id"]
    return {"categoria": cat, "bandeja": plato_a, "sopa": plato_b}
