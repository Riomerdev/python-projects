# DataSync

ETL incremental que importa registros de una API pública a SQLite. Guarda el último identificador confirmado, escribe cada página en una transacción y reintenta fallos temporales con backoff exponencial.

**Lenguaje:** Python  
**Stack:** httpx, asyncio, SQLite  
**Caso de uso:** alimentar un almacén operacional desde una API externa sin duplicar ni perder páginas tras una interrupción.

## Ejecutar

~~~bash
cd projects/data-sync
python -m venv .venv
. .venv/bin/activate
pip install -e .
python -m data_sync.cli --database .data/posts.sqlite3 --batch-size 25
~~~

La fuente predeterminada es JSONPlaceholder y el ejemplo no requiere credenciales. También puedes pasar --base-url a una API compatible con el mismo formato de posts.
