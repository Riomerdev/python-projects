from __future__ import annotations

import argparse
import asyncio
import sqlite3
from pathlib import Path
from typing import Any

import httpx


def prepare_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                synced_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )


def last_id(path: Path) -> int:
    with sqlite3.connect(path) as connection:
        row = connection.execute("SELECT COALESCE(MAX(id), 0) FROM posts").fetchone()
    return int(row[0])


async def fetch_page(client: httpx.AsyncClient, url: str, start: int, limit: int) -> list[dict[str, Any]]:
    for attempt in range(5):
        response = await client.get(url.rstrip("/") + "/posts", params={"_start": start, "_limit": limit})
        if response.status_code == 429 or response.status_code >= 500:
            if attempt == 4:
                response.raise_for_status()
            await asyncio.sleep(min(2**attempt, 16))
            continue
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("API response must be a JSON array")
        return payload
    return []


async def sync(base_url: str, database: Path, batch_size: int, max_pages: int) -> int:
    prepare_database(database)
    cursor = last_id(database)
    inserted = 0

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0), headers={"User-Agent": "riomer-data-sync/1.0"}) as client:
        for _ in range(max_pages):
            page = await fetch_page(client, base_url, cursor, batch_size)
            if not page:
                break
            with sqlite3.connect(database) as connection:
                connection.executemany(
                    """INSERT INTO posts(id, user_id, title, body)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(id) DO UPDATE SET
                         user_id=excluded.user_id,
                         title=excluded.title,
                         body=excluded.body,
                         synced_at=CURRENT_TIMESTAMP""",
                    [
                        (int(item["id"]), int(item["userId"]), str(item["title"]), str(item["body"]))
                        for item in page
                    ],
                )
            inserted += len(page)
            cursor = max(int(item["id"]) for item in page)
            if len(page) < batch_size:
                break
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza posts de una API paginada a SQLite.")
    parser.add_argument("--base-url", default="https://jsonplaceholder.typicode.com")
    parser.add_argument("--database", type=Path, default=Path(".data/posts.sqlite3"))
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--max-pages", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 100:
        parser.error("--batch-size must be between 1 and 100")
    if args.max_pages < 1:
        parser.error("--max-pages must be positive")
    try:
        count = asyncio.run(sync(args.base_url, args.database, args.batch_size, args.max_pages))
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        parser.exit(2, f"data-sync: {exc}\n")
    print(f"Sincronización completa: {count} registros procesados; checkpoint={last_id(args.database)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
