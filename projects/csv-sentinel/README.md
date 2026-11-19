# CSV Sentinel

Herramienta de control de calidad para archivos recibidos de proveedores u otros sistemas. Valida encabezados y tipos, limpia espacios, separa filas buenas de filas rechazadas y genera un reporte JSON con los motivos.

**Lenguaje:** Python  
**Dependencias:** biblioteca estándar  
**Caso de uso:** impedir que un archivo defectuoso contamine una importación de inventario, pagos o clientes.

## Ejecutar

Desde esta carpeta:

~~~bash
python -m csv_sentinel.cli examples/orders.csv --schema examples/schema.json --output out/clean.csv
~~~

El programa crea out/clean.csv, out/clean.rejected.csv y out/clean.report.json. El comando devuelve código 1 cuando encuentra filas rechazadas, para que un job de automatización pueda detener la importación y alertar al operador.

El esquema admite campos obligatorios, tipos integer, decimal, date y boolean, y mínimos numéricos. El ejemplo incluye una orden válida y otra con precio inválido.
