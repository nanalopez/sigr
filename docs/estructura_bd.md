# Estructura de la base de datos (SQLite)

El esquema se crea automáticamente al iniciar la aplicación (`sigr/db.py`, constante `SCHEMA`).

| Tabla | Propósito | Restricciones principales |
|---|---|---|
| `users` | Cuentas de clientes, meseros y administradores | `username` único; `role` ∈ {cliente, mesero, administrador} |
| `categories` | Categorías del menú | `name` único |
| `dishes` | Platos del menú | `price >= 0`; `available` ∈ {0, 1}; FK a `categories` |
| `orders` | Encabezado del pedido | `status` ∈ {recibido, en_preparacion, listo, entregado, cancelado}; `total` calculado en servidor |
| `order_items` | Líneas del pedido | `quantity > 0`; guarda `unit_price` para conservar el precio histórico |
| `reservations` | Reservas por fecha y hora | `people > 0`; `status` ∈ {activa, cancelada} |
| `cash_closings` | Cierre diario de caja | `date` único (un cierre por día) |

Relaciones: `dishes.category_id → categories.id`; `orders.user_id → users.id`; `order_items.order_id → orders.id`; `order_items.dish_id → dishes.id`; `reservations.user_id → users.id`; `cash_closings.closed_by → users.id`.

**Nota sobre fechas:** los pedidos guardan `created_at` con la hora local del servidor (`YYYY-MM-DDTHH:MM:SS`). El día de negocio se toma de los primeros 10 caracteres, por lo que el servidor debe configurarse con la zona horaria del restaurante.
