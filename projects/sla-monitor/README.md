# SLA Monitor

Monitor asíncrono de endpoints HTTP para un equipo de operaciones. Ejecuta checks periódicos, conserva el historial en SQLite y expone disponibilidad y percentil de latencia por objetivo.

**Lenguaje:** Python  
**Stack:** FastAPI, httpx, asyncio, SQLite  
**Caso de uso:** detectar degradaciones y revisar el cumplimiento de un SLA interno sin depender de un proveedor externo.

## Ejecutar

~~~bash
cd projects/sla-monitor
python -m venv .venv
. .venv/bin/activate
pip install -e .
MONITORED_URLS="https://example.com/health" uvicorn sla_monitor.app:app --reload
~~~

En PowerShell configura $env:MONITORED_URLS="https://example.com/health". Abre /docs para explorar la API, /summary para ver las métricas y /history para revisar los checks recientes.

La demo no envía alertas ni datos a terceros. El intervalo y la lista de endpoints se configuran por variables de entorno.
