# Data Quality API

Servicio de ingesta de pedidos CSV para detectar problemas antes de que contaminen un sistema operativo. Cada carga genera un resumen, conserva las filas válidas en PostgreSQL y guarda las rechazadas con número de fila y motivo para que el equipo pueda corregirlas.

## Tecnologías y criterios

Python 3.12, FastAPI, SQLAlchemy 2.1, Alembic, Psycopg 3, PostgreSQL 18, Docker Compose y GitHub Actions. Incluye contratos OpenAPI, límites de tamaño, transacciones, claves únicas, migraciones versionadas y logs estructurados.

## Ejecutar con Docker

~~~powershell
Copy-Item .env.example .env
# Edit .env and set POSTGRES_PASSWORD to a local password.
docker compose up --build
~~~

La aplicación ejecuta alembic upgrade head y queda en http://localhost:8000. La documentación interactiva está en /docs; la salud de API y base en /health. PostgreSQL queda en el puerto local 5434. Envía el ejemplo incluido:

~~~sh
curl -F "file=@examples/orders.csv" http://localhost:8000/api/imports
~~~

Consulta el historial en GET /api/imports, el detalle en GET /api/imports/{id} y los registros aceptados en GET /api/orders. El CSV exige external_id, sku, quantity y unit_price. Las claves repetidas dentro de un archivo o ya aceptadas se mandan a cuarentena.

## Desarrollo local

Requiere Python 3.12 y PostgreSQL. Instala con pip install -e ., configura DATABASE_URL usando la contraseña local, ejecuta alembic upgrade head y después uvicorn data_quality_api.main:app --reload. .env.example enumera la variable requerida.

## Alcance

El servicio conserva el archivo original solo como nombre y resumen; no guarda cargas completas ni expone rutas del sistema. El límite es 1 MB y la API no tiene autenticación para que la demo local arranque fácilmente. Antes de desplegar, añade autenticación, cifrado, retención configurable, cuotas y protección de datos personales.

## English

CSV order-ingestion service with row-level validation, PostgreSQL persistence, an auditable quarantine, versioned schema migrations and OpenAPI docs. Invalid rows remain reviewable, and duplicate external identifiers cannot be accepted twice.
