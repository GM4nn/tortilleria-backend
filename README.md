# Tortillería — Backend (FastAPI REST)

API web que reutiliza la lógica del sistema de escritorio, siguiendo la estructura
del *backend guide* (core + src/{models,providers,schemas,routers}), pero en REST.

## Estructura

```
app/
├── main.py                 # FastAPI, CORS, manejo de errores, create_all al iniciar
├── requirements.txt
├── core/
│   ├── config.py           # Settings (.env) + DATABASE_URI
│   ├── database.py         # engine, SessionLocal, get_db (dependency)
│   └── base.py             # Base declarativa (id, created_at, updated_at)
└── src/
    ├── models/             # entidades SQLAlchemy
    ├── schemas/            # DTOs Pydantic (entrada/salida)
    ├── providers/          # datos + lógica (reciben la Session)
    ├── services/           # integraciones externas (Firestore)
    └── routers/            # endpoints REST (un archivo por recurso)
```

Cada recurso = `model → schema → provider → router` + `include_router` en `main`.
El `provider` recibe la `Session` (inyectada con `Depends(get_db)`), consulta y la
capa `get_db` la cierra al terminar la request.

## Correr en local

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r app/requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

- API: http://localhost:8000/api
- Docs (Swagger): http://localhost:8000/docs
- OpenAPI (para generar el cliente TS del frontend): http://localhost:8000/openapi.json

## Base de datos

SQLite (mismo patrón que la guía; cambiar a Postgres es solo el `DATABASE_URI` en
`core/config.py`). Ajusta `DATABASE_PATH` en `.env`.

## Firestore (opcional)

Si defines `FIREBASE_CREDENTIALS_PATH`, sincroniza los repartidores a la colección
`dealers` (login de la app móvil). Vacío = desactivado.

## Recursos (todos bajo `/api`)

- `dealers` — repartidores (CRUD) + sync a Firestore.
- `customers` — clientes (CRUD) + `customers/{id}/prices` (precios personalizados).
- `products` — productos/inventario (CRUD).
- `suppliers` — proveedores (CRUD).
- `orders` — pedidos: crear, listar (`?today=true`), detalle, `{id}/payment`,
  `{id}/complete`, `{id}/cancel` + sync a Firestore (para la app móvil).
- `sales` — ventas: crear, listar, detalle, `sales/today`.
- `cash` — caja: `cash/summary`, `cash/today`, historial, crear corte.
- `supplies` — insumos (CRUD) + `supplies/{id}/purchases` (compras).
- `reports` — `reports/today`, `top-products`, `top-customers`, `monthly-income`.
- `assistant` — `assistant/ask` (asistente IA con Claude; requiere ANTHROPIC_API_KEY).
