# Webhook Gateway

Receptor de webhooks para integraciones de comercio y facturación. Verifica la firma HMAC sobre el cuerpo original, exige un identificador del evento, guarda la entrega en SQLite y deduplica reintentos del proveedor.

**Lenguaje:** Python  
**Stack:** FastAPI, SQLite, HMAC-SHA256  
**Caso de uso:** recibir eventos externos sin procesar dos veces una misma orden o pago.

## Ejecutar

~~~bash
cd projects/webhook-gateway
python -m venv .venv
. .venv/bin/activate
pip install -e .
export WEBHOOK_SECRET="local-demo-secret"
uvicorn webhook_gateway.app:app --reload
~~~

En Windows PowerShell, activa el entorno con .venv\Scripts\Activate.ps1 y configura la variable con $env:WEBHOOK_SECRET.

La documentación OpenAPI queda en /docs. Envía X-Event-Id y X-Signature-SHA256. La firma es sha256= seguido del HMAC hexadecimal del cuerpo HTTP exacto.
