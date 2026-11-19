from __future__ import annotations

import asyncio
import os
import sqlite3
import time
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import quantiles
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Query


DATABASE_PATH = Path(os.getenv("SLA_DATABASE", ".data/sla.sqlite3"))
MONITORED_URLS = [value.strip() for value in os.getenv("MONITORED_URLS", "").split(",") if value.strip()]
INTERVAL_SECONDS = max(10, int(os.getenv("CHECK_INTERVAL_SECONDS", "60")))
TIMEOUT_SECONDS = max(1.0, float(os.getenv("CHECK_TIMEOUT_SECONDS", "8")))


def connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize() -> None:
    with connect() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                checked_at TEXT NOT NULL,
                status_code INTEGER,
                latency_ms REAL NOT NULL,
                healthy INTEGER NOT NULL,
                error TEXT
            )"""
        )
        connection.execute("CREATE INDEX IF NOT EXISTS ix_checks_target_time ON checks(target, checked_at)")


async def record_target(client: httpx.AsyncClient, url: str) -> None:
    started = time.perf_counter()
    status_code: int | None = None
    error: str | None = None
    healthy = False
    try:
        response = await client.get(url)
        status_code = response.status_code
        healthy = response.is_success
    except httpx.HTTPError as exc:
        error = type(exc).__name__
    latency = (time.perf_counter() - started) * 1000
    with connect() as connection:
        connection.execute(
            """INSERT INTO checks(target, checked_at, status_code, latency_ms, healthy, error)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (url, datetime.now(UTC).isoformat(), status_code, latency, int(healthy), error),
        )


async def check_once() -> None:
    if not MONITORED_URLS:
        return
    timeout = httpx.Timeout(TIMEOUT_SECONDS)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        await asyncio.gather(*(record_target(client, url) for url in MONITORED_URLS))


async def monitor_loop() -> None:
    while True:
        await check_once()
        await asyncio.sleep(INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize()
    task = asyncio.create_task(monitor_loop())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="SLA Monitor", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/targets")
def targets() -> list[dict[str, str]]:
    return [
        {"url": url, "name": urlparse(url).netloc or url}
        for url in MONITORED_URLS
    ]


@app.get("/summary")
def summary(hours: int = Query(default=24, ge=1, le=720)) -> dict[str, object]:
    since = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()
    with connect() as connection:
        rows = connection.execute(
            """SELECT target, COUNT(*) AS checks, SUM(healthy) AS successful,
                      AVG(latency_ms) AS avg_latency, MAX(checked_at) AS last_checked
               FROM checks WHERE checked_at >= ? GROUP BY target ORDER BY target""",
            (since,),
        ).fetchall()
        latencies = [
            float(row[0])
            for row in connection.execute(
                "SELECT latency_ms FROM checks WHERE checked_at >= ? ORDER BY latency_ms", (since,)
            ).fetchall()
        ]

    p95 = None
    if latencies:
        p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))]
    targets_summary = []
    for row in rows:
        total = int(row["checks"])
        successful = int(row["successful"] or 0)
        targets_summary.append(
            {
                "url": row["target"],
                "checks": total,
                "availability_percent": round(successful / total * 100, 2),
                "average_latency_ms": round(float(row["avg_latency"]), 2),
                "last_checked": row["last_checked"],
            }
        )
    return {"window_hours": hours, "p95_latency_ms": round(p95, 2) if p95 is not None else None,
            "targets": targets_summary}


@app.get("/history")
def history(target: str, limit: int = Query(default=100, ge=1, le=1000)) -> list[dict[str, object]]:
    if target not in MONITORED_URLS:
        raise HTTPException(status_code=404, detail="Target is not configured")
    with connect() as connection:
        rows = connection.execute(
            """SELECT checked_at, status_code, latency_ms, healthy, error
               FROM checks WHERE target=? ORDER BY checked_at DESC LIMIT ?""",
            (target, limit),
        ).fetchall()
    return [dict(row) for row in rows]
