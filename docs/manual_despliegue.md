# Manual de despliegue

## Requisitos
- Python 3.11 o superior.
- Git (para clonar el repositorio).

## Instalación local
```bash
git clone https://github.com/<usuario>/sigr.git
cd sigr
python -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Variables de entorno
| Variable | Obligatoria | Descripción |
|---|---|---|
| `SIGR_SECRET_KEY` | Sí en producción | Clave para firmar las sesiones. |
| `SIGR_DB` | No | Ruta del archivo SQLite (por defecto `instance/sigr.db`). |
| `SIGR_MAX_RESERVAS` | No | Reservas máximas por horario (por defecto 5). |
| `SIGR_ADMIN_USER` / `SIGR_ADMIN_PASSWORD` | No | Crea el administrador inicial si aún no existe. |

## Ejecución
```bash
export SIGR_SECRET_KEY="una-clave-larga-y-secreta"
export SIGR_ADMIN_USER="admin"
export SIGR_ADMIN_PASSWORD="cambiar-esta-clave"
flask --app sigr run
```

## Pruebas
```bash
pytest -q
```

## Verificación rápida
1. `POST /api/auth/login` con el administrador debe responder 200.
2. `GET /api/dishes` debe responder 200 (lista vacía al inicio).
