import csv
import io
import re
from decimal import Decimal, InvalidOperation
from typing import Any

REQUIRED_COLUMNS = {"external_id", "sku", "quantity", "unit_price"}
SKU_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._-]{1,39}$")


def parse_csv(payload: bytes) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    headers = {header.strip() for header in (reader.fieldnames or []) if header}
    missing = sorted(REQUIRED_COLUMNS - headers)
    if missing:
        raise ValueError("Faltan columnas requeridas: " + ", ".join(missing))
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row_number, raw in enumerate(reader, start=2):
        row = {(key or "").strip(): (value or "").strip() for key, value in raw.items()}
        errors: list[str] = []
        external_id = row.get("external_id", "")
        sku = row.get("sku", "").upper()
        if not external_id or len(external_id) > 80:
            errors.append("external_id debe tener entre 1 y 80 caracteres")
        if not SKU_PATTERN.fullmatch(sku):
            errors.append("sku debe tener entre 2 y 40 caracteres alfanuméricos")
        if external_id and external_id in seen:
            errors.append("external_id duplicado en el archivo")
        if external_id:
            seen.add(external_id)
        try:
            quantity = int(row.get("quantity", ""))
            if quantity <= 0:
                errors.append("quantity debe ser mayor que cero")
        except ValueError:
            quantity = 0
            errors.append("quantity debe ser un entero")
        try:
            unit_price = Decimal(row.get("unit_price", "")).quantize(Decimal("0.01"))
            if not unit_price.is_finite() or unit_price < 0 or unit_price >= Decimal("10000000000"):
                errors.append("unit_price debe estar entre cero y 9.999.999.999,99")
        except (InvalidOperation, ValueError):
            unit_price = Decimal("0")
            errors.append("unit_price debe ser un importe decimal válido")
        if errors:
            rejected.append({"row_number": row_number, "external_id": external_id or None, "messages": errors})
        else:
            accepted.append({"external_id": external_id, "sku": sku, "quantity": quantity,
                "unit_price": unit_price, "_row_number": row_number})
    return accepted, rejected
