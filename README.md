# SIGR — Sistema Integral de Gestión de Restaurante

Aplicación web para gestionar pedidos, reservas, menú digital, cierre de caja y reportes de ventas diarios. Es la **línea base** del proyecto de la asignatura Gestión del Software (Unidad 2, Gestión de la configuración).

## Módulos
- **Autenticación:** clientes, meseros y administradores, con control de roles.
- **Menú digital:** CRUD de categorías y platos.
- **Pedidos:** registro con total calculado en el servidor y seguimiento de estados.
- **Reservas:** por fecha y hora, con límite de reservas por horario.
- **Cierre de caja y reportes:** cierre diario y reporte de ventas por día.

## Inicio rápido
```bash
pip install -r requirements.txt
pytest -q
flask --app sigr run
```

Consulte [docs/manual_despliegue.md](docs/manual_despliegue.md) para la configuración completa y [docs/estructura_bd.md](docs/estructura_bd.md) para el modelo de datos.

## API (resumen)
| Método | Ruta | Rol |
|---|---|---|
| POST | `/api/auth/register`, `/api/auth/login`, `/api/auth/logout` | Público |
| GET | `/api/auth/me` | Cualquiera con sesión |
| POST | `/api/users` | administrador |
| GET / POST | `/api/categories` | público / administrador |
| GET / POST / PUT / DELETE | `/api/dishes` | público / administrador |
| POST / GET | `/api/orders` | cliente, mesero (crear); según rol (listar) |
| PATCH | `/api/orders/<id>/status` | mesero, administrador |
| POST / GET / DELETE | `/api/reservations` | cliente, mesero, administrador |
| POST / GET | `/api/cash-closings` | administrador |
| GET | `/api/reports/daily?date=AAAA-MM-DD` | administrador |

## Licencia
MIT. Véase [LICENSE](LICENSE).
