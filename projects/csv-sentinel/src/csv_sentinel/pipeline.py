from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class PipelineError(ValueError):
    """Raised when the input file or schema cannot be processed."""


def _validate_type(value: str, expected: str) -> str | None:
    normalized = value.strip()
    try:
        if expected == "integer":
            int(normalized)
        elif expected == "decimal":
            Decimal(normalized)
        elif expected == "date":
            date.fromisoformat(normalized)
        elif expected == "boolean":
            if normalized.casefold() not in {"true", "false", "1", "0", "yes", "no"}:
                return "must be true/false, 1/0, or yes/no"
        else:
            return f"unsupported type: {expected}"
    except (ValueError, InvalidOperation):
        return f"must be a valid {expected}"
    return None


def _row_errors(row: dict[str, str | None], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = schema.get("required", [])
    types = schema.get("types", {})
    minimums = schema.get("minimums", {})

    for field in required:
        if not (row.get(field) or "").strip():
            errors.append(f"{field}: required value is empty")

    for field, expected in types.items():
        value = (row.get(field) or "").strip()
        if value:
            reason = _validate_type(value, expected)
            if reason:
                errors.append(f"{field}: {reason}")

    for field, minimum in minimums.items():
        value = (row.get(field) or "").strip()
        if value:
            try:
                if Decimal(value) < Decimal(str(minimum)):
                    errors.append(f"{field}: must be at least {minimum}")
            except InvalidOperation:
                pass

    return errors


def run_pipeline(input_path: Path, schema_path: Path, output_path: Path) -> dict[str, Any]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise PipelineError("schema root must be a JSON object")

    with input_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        headers = reader.fieldnames
        if not headers:
            raise PipelineError("input CSV is empty or has no header")
        if len(headers) != len(set(headers)):
            raise PipelineError("input CSV contains duplicate column names")

        missing = sorted(set(schema.get("required", [])) - set(headers))
        missing += sorted(set(schema.get("types", {})) - set(headers))
        if missing:
            raise PipelineError(f"schema columns are missing from CSV: {', '.join(sorted(set(missing)))}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        rejected_path = output_path.with_name(f"{output_path.stem}.rejected{output_path.suffix}")
        report_path = output_path.with_suffix(".report.json")
        accepted = 0
        rejected = 0
        errors_by_field: Counter[str] = Counter()

        with output_path.open("w", newline="", encoding="utf-8") as clean_file, rejected_path.open(
            "w", newline="", encoding="utf-8"
        ) as rejected_file:
            clean_writer = csv.DictWriter(clean_file, fieldnames=headers)
            rejected_writer = csv.DictWriter(rejected_file, fieldnames=[*headers, "_errors"])
            clean_writer.writeheader()
            rejected_writer.writeheader()

            for row in reader:
                cleaned = {key: (value or "").strip() for key, value in row.items() if key}
                errors = _row_errors(cleaned, schema)
                if errors:
                    rejected += 1
                    for error in errors:
                        errors_by_field[error.split(":", 1)[0]] += 1
                    rejected_writer.writerow({**cleaned, "_errors": " | ".join(errors)})
                else:
                    accepted += 1
                    clean_writer.writerow(cleaned)

    report = {
        "input": str(input_path),
        "clean_output": str(output_path),
        "rejected_output": str(rejected_path),
        "rows_accepted": accepted,
        "rejected_rows": rejected,
        "errors_by_field": dict(sorted(errors_by_field.items())),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
