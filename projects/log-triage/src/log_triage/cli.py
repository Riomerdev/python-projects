from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fingerprint(event: dict[str, Any]) -> str:
    return "|".join(
        str(event.get(key, "unknown")).strip()
        for key in ("service", "level", "error_code", "message")
    )


def summarize(path: Path) -> dict[str, Any]:
    services: Counter[str] = Counter()
    levels: Counter[str] = Counter()
    fingerprints: Counter[str] = Counter()
    first_seen: dict[str, str] = {}
    last_seen: dict[str, str] = {}
    malformed = 0
    total = 0

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict) or not event.get("timestamp"):
                raise ValueError("event must be an object with timestamp")
            parse_time(str(event["timestamp"]))
        except (json.JSONDecodeError, ValueError, TypeError):
            malformed += 1
            continue

        total += 1
        service = str(event.get("service", "unknown"))
        level = str(event.get("level", "unknown")).upper()
        key = fingerprint(event)
        services[service] += 1
        levels[level] += 1
        fingerprints[key] += 1
        first_seen[key] = min(first_seen.get(key, str(event["timestamp"])), str(event["timestamp"]))
        last_seen[key] = max(last_seen.get(key, str(event["timestamp"])), str(event["timestamp"]))

    ranked = [
        {
            "fingerprint": key,
            "count": count,
            "first_seen": first_seen[key],
            "last_seen": last_seen[key],
        }
        for key, count in fingerprints.most_common(20)
    ]
    return {
        "source": str(path),
        "total_events": total,
        "malformed_lines": malformed,
        "events_by_service": dict(sorted(services.items())),
        "events_by_level": dict(sorted(levels.items())),
        "top_fingerprints": ranked,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume logs JSONL para análisis de incidentes.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = summarize(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['total_events']} eventos; {report['malformed_lines']} líneas inválidas")
    print(f"Informe: {args.output}")
    return 1 if report["malformed_lines"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
