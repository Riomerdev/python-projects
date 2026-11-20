# Python Projects

Portafolio de herramientas profesionales en **Python**. Cada solución está separada por problema de negocio y se puede ejecutar por su cuenta.

| Proyecto | Uso | Ejecutar |
|---|---|---|
| CSV Sentinel | Validar y depurar entregas CSV antes de cargarlas a un sistema | projects/csv-sentinel |
| Webhook Gateway | Recibir eventos firmados de proveedores y evitar duplicados | projects/webhook-gateway |
| PolicySearch | Encontrar procedimientos con referencias a su documento de origen | projects/policy-search |
| LogTriage | Resumir incidentes a partir de logs estructurados | projects/log-triage |
| DataSync | Sincronizar datos públicos a SQLite con checkpoint incremental | projects/data-sync |
| SLA Monitor | Medir disponibilidad y latencia de servicios HTTP | projects/sla-monitor |
| Data Quality API | Validar cargas CSV con cuarentena auditable en PostgreSQL | projects/data-quality-api |

## Convenciones

Los proyectos usan Python 3.12 o superior, configuración reproducible por proyecto y datos de demostración ficticios. Los servicios HTTP incluyen documentación OpenAPI. No se requieren credenciales reales para los ejemplos locales. Data Quality API incluye migraciones Alembic, OpenAPI y un entorno local en Docker Compose.

