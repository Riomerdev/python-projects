import logging
import os
from contextlib import asynccontextmanager
from uuid import UUID

import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_session
from .models import AcceptedOrder, ImportIssue, ImportRun
from .validation import parse_csv

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}')
logger = logging.getLogger("data_quality_api")
MAX_UPLOAD_BYTES = 1_000_000


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("data quality API started")
    yield
    logger.info("data quality API stopped")


app = FastAPI(title="Data Quality API", version="1.0.0",
    description="CSV ingestion with auditable row-level validation and quarantine.", lifespan=lifespan)


@app.get("/health")
def health(session: Session = Depends(get_session)) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@app.post("/api/imports", status_code=201)
async def create_import(file: UploadFile = File(...), session: Session = Depends(get_session)) -> dict[str, object]:
    filename = (file.filename or "upload.csv").replace("\\", "/").split("/")[-1][:180]
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Solo se aceptan archivos CSV.")
    payload = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="El CSV supera el límite de 1 MB.")
    try:
        accepted_rows, rejected_rows = parse_csv(payload)
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="El archivo debe estar codificado en UTF-8.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    run = ImportRun(filename=filename,
        status="COMPLETED" if not rejected_rows else "PARTIAL",
        rows_total=len(accepted_rows) + len(rejected_rows),
        rows_accepted=len(accepted_rows), rows_rejected=len(rejected_rows))
    session.add(run)
    session.flush()
    external_ids = [row["external_id"] for row in accepted_rows]
    existing_ids = set(session.scalars(
        select(AcceptedOrder.external_id).where(AcceptedOrder.external_id.in_(external_ids))
    ).all()) if external_ids else set()
    for row in accepted_rows:
        row_number = row.pop("_row_number")
        if row["external_id"] in existing_ids:
            rejected_rows.append({"row_number": row_number, "external_id": row["external_id"],
                "messages": ["external_id ya fue importado anteriormente"]})
            run.rows_accepted -= 1
            run.rows_rejected += 1
            continue
        session.add(AcceptedOrder(import_id=run.id, **row))
    for issue in rejected_rows:
        session.add(ImportIssue(import_id=run.id, row_number=issue["row_number"],
            external_id=issue["external_id"], messages="; ".join(issue["messages"])))
    if run.rows_rejected:
        run.status = "PARTIAL" if run.rows_accepted else "REJECTED"
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        logger.warning("concurrent duplicate import rejected")
        raise HTTPException(status_code=409, detail="Un registro fue importado en paralelo; vuelve a cargar el archivo.") from exc
    session.refresh(run)
    return {"id": str(run.id), "filename": run.filename, "status": run.status,
        "rows_total": run.rows_total, "rows_accepted": run.rows_accepted, "rows_rejected": run.rows_rejected}


@app.get("/api/imports")
def list_imports(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    runs = session.scalars(select(ImportRun).order_by(ImportRun.created_at.desc()).limit(100)).all()
    return [{"id": str(run.id), "filename": run.filename, "status": run.status,
        "rows_total": run.rows_total, "rows_accepted": run.rows_accepted,
        "rows_rejected": run.rows_rejected, "created_at": run.created_at.isoformat()} for run in runs]


@app.get("/api/imports/{run_id}")
def get_import(run_id: UUID, session: Session = Depends(get_session)) -> dict[str, object]:
    run = session.get(ImportRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Importación no encontrada.")
    return {"id": str(run.id), "filename": run.filename, "status": run.status,
        "rows_total": run.rows_total, "rows_accepted": run.rows_accepted,
        "rows_rejected": run.rows_rejected, "created_at": run.created_at.isoformat(),
        "issues": [{"row_number": issue.row_number, "external_id": issue.external_id,
            "messages": issue.messages} for issue in sorted(run.issues, key=lambda item: item.row_number)]}


@app.get("/api/orders")
def list_accepted_orders(session: Session = Depends(get_session)) -> list[dict[str, object]]:
    rows = session.scalars(select(AcceptedOrder).order_by(AcceptedOrder.external_id).limit(500)).all()
    return [{"external_id": row.external_id, "sku": row.sku, "quantity": row.quantity,
        "unit_price": str(row.unit_price), "import_id": str(row.import_id)} for row in rows]


def run() -> None:
    uvicorn.run("data_quality_api.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
