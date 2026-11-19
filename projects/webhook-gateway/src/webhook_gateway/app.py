from __future__ import annotations

import json
import os
import re
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, Response

from webhook_gateway.security import verify_signature
from webhook_gateway.store import EventStore


DATABASE_PATH = os.getenv("WEBHOOK_DATABASE", ".data/webhooks.sqlite3")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
EVENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
store = EventStore(DATABASE_PATH)
app = FastAPI(
    title="Webhook Gateway",
    version="1.0.0",
    description="Signed, idempotent webhook intake with durable SQLite storage.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhooks/{source}", status_code=202)
async def receive_webhook(
    source: str,
    request: Request,
    response: Response,
    event_id: str | None = Header(default=None, alias="X-Event-Id"),
    signature: str | None = Header(default=None, alias="X-Signature-SHA256"),
) -> dict[str, Any]:
    if not WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook secret is not configured")
    if not event_id or not EVENT_ID_PATTERN.fullmatch(event_id):
        raise HTTPException(status_code=400, detail="A valid X-Event-Id header is required")

    raw_body = await request.body()
    if not verify_signature(raw_body, signature, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Body must contain valid JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="JSON body must be an object")

    created = store.accept(source, event_id, payload)
    response.status_code = 202 if created else 200
    return {"accepted": True, "duplicate": not created, "source": source, "event_id": event_id}


@app.get("/events")
def list_events(limit: int = 50) -> list[dict[str, Any]]:
    if not 1 <= limit <= 200:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 200")
    return store.list_events(limit)


@app.get("/events/{source}/{event_id}")
def get_event(source: str, event_id: str) -> dict[str, Any]:
    event = store.get_event(source, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
