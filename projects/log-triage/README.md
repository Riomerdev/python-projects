# LogTriage

Analizador para guardias de soporte que recibe logs JSONL, agrupa eventos repetidos y prioriza fingerprints por volumen y nivel. También informa líneas inválidas, para que errores de formato no desaparezcan silenciosamente.

**Lenguaje:** Python  
**Dependencias:** biblioteca estándar  
**Caso de uso:** convertir miles de líneas de logs en un resumen operativo que se pueda adjuntar a un incidente.

## Ejecutar

~~~bash
cd projects/log-triage
python -m log_triage.cli examples/service.jsonl --output out/incident-report.json
~~~

El informe contiene volumen por servicio y nivel, fingerprints más frecuentes y cantidad de líneas que no se pudieron interpretar. Los timestamps deben incluir zona horaria ISO-8601.
