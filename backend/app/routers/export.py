"""Preview, export, and download endpoints."""

from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..models.schemas import (
    ExportRequest,
    ExportResponse,
    PreviewData,
    PreviewRequest,
    PreviewResponse,
)
from ..services.data_extractor import DATA_TYPE_DISPLAY, build_trial_balance
from ..services.exporters.csv_exporter import export_csv
from ..services.exporters.json_exporter import export_json
from ..services.exporters.parquet_exporter import export_parquet
from ..services.exporters.xlsx_exporter import export_xlsx
from ..services.session_manager import session_manager
from ..utils.security import safe_path, validate_uuid

logger = logging.getLogger(__name__)

router = APIRouter()

PREVIEW_ROWS = 20

# MIME types for downloads
MIME_TYPES = {
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".json": "application/json",
    ".parquet": "application/octet-stream",
    ".zip": "application/zip",
}


@router.post("/preview", response_model=PreviewResponse)
async def preview(body: PreviewRequest) -> PreviewResponse:
    """Preview rows of selected data types with optional search and pagination."""
    if not validate_uuid(body.session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format.")

    session = session_manager.get_session(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    if not body.data_types:
        raise HTTPException(status_code=422, detail="No data types selected.")

    search_term = (body.search or "").strip().lower()
    page = max(1, body.page)
    page_size = max(1, min(body.page_size, 200))  # cap at 200

    previews = []
    for dt in body.data_types:
        rows = session.parsed_data.get(dt)
        if rows is None:
            continue

        # Filter rows if search term provided
        if search_term:
            filtered = [
                row for row in rows
                if any(
                    search_term in str(v).lower()
                    for v in row.values()
                    if v is not None
                )
            ]
        else:
            filtered = rows

        total_count = len(filtered)
        columns = list(rows[0].keys()) if rows else []

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        page_rows = filtered[start:end]

        previews.append(PreviewData(
            data_type=dt,
            columns=columns,
            rows=page_rows,
            total_count=total_count,
        ))

    return PreviewResponse(session_id=body.session_id, previews=previews)


@router.post("/export", response_model=ExportResponse)
async def export_data(body: ExportRequest) -> ExportResponse:
    """Export selected data types to chosen format."""
    if not validate_uuid(body.session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format.")

    session = session_manager.get_session(body.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    if not body.data_types:
        raise HTTPException(status_code=422, detail="No data types selected.")

    export_format = body.format.lower()
    if export_format not in ("csv", "xlsx", "json", "parquet"):
        raise HTTPException(status_code=422, detail="Invalid export format.")

    # Collect requested data
    data_to_export: dict[str, list[dict[str, Any]]] = {}
    for dt in body.data_types:
        rows = session.parsed_data.get(dt)
        if rows is not None:
            display = DATA_TYPE_DISPLAY.get(dt, dt)
            data_to_export[display] = rows

    if not data_to_export:
        raise HTTPException(status_code=422, detail="No data available for selected types.")

    # Create export subdirectory
    export_dir = safe_path(session.temp_dir, "exports")
    os.makedirs(export_dir, exist_ok=True)

    # Build base filename: {year}-{company}-{YYYYMMDDHHMM}
    base_name = _build_base_name(session.fiscal_year, session.company_name)

    # Run export
    try:
        if export_format == "csv":
            filename = export_csv(data_to_export, export_dir, base_name)
        elif export_format == "xlsx":
            trial_balance = build_trial_balance(session.parsed_data)
            filename = export_xlsx(data_to_export, export_dir, base_name,
                                   validation_checks=session.validation_checks or None,
                                   trial_balance=trial_balance)
        elif export_format == "json":
            filename = export_json(data_to_export, export_dir, base_name)
        elif export_format == "parquet":
            filename = export_parquet(data_to_export, export_dir, base_name)
        else:
            raise HTTPException(status_code=422, detail="Invalid format.")
    except Exception as exc:
        logger.exception("Export error")
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")

    download_url = f"/api/download/{body.session_id}/{filename}"

    return ExportResponse(
        session_id=body.session_id,
        filename=filename,
        download_url=download_url,
        format=export_format,
        data_types=body.data_types,
    )


@router.get("/download/{session_id}/{filename}")
async def download_file(session_id: str, filename: str) -> FileResponse:
    """Download an exported file."""
    if not validate_uuid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format.")

    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    # Validate filename (only allow specific safe characters)
    safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._- &")
    if not all(c in safe_chars for c in filename):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    # Resolve path safely
    try:
        filepath = safe_path(session.temp_dir, "exports", filename)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path.")

    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File not found.")

    # Determine MIME type
    _, ext = os.path.splitext(filename.lower())
    media_type = MIME_TYPES.get(ext, "application/octet-stream")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_base_name(fiscal_year: str, company_name: str) -> str:
    """Build export filename base: {year}-{company}-{YYYYMMDDHHMM}.

    Sanitizes inputs to produce a safe filename containing only alphanumeric,
    dash, underscore, and dot characters.
    """
    year = _sanitize_for_filename(fiscal_year) or "unknown"
    company = _sanitize_for_filename(company_name) or "unknown"
    timestamp = datetime.now(tz=None).strftime("%Y%m%d%H%M")
    return f"{year}-{company}-{timestamp}"


def _sanitize_for_filename(value: str) -> str:
    """Sanitize a string for safe use in a filename.

    Replaces any character that is not alphanumeric, dot, dash, or underscore
    with an underscore. Collapses consecutive underscores and strips leading/
    trailing underscores. Caps length at 40.
    """
    if not value:
        return ""
    # Replace unsafe chars with underscore
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", value)
    # Collapse repeated underscores
    sanitized = re.sub(r"_+", "_", sanitized)
    # Strip leading/trailing underscores, dots, dashes
    sanitized = sanitized.strip("_.-")
    return sanitized[:40]
