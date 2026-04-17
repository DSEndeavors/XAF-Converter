"""Session info and restart endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException

from ..models.schemas import (
    DataTypeInfo,
    FileInfo,
    RestartRequest,
    RestartResponse,
    SessionResponse,
)
from ..services.data_extractor import DATA_TYPE_DISPLAY, get_record_counts
from ..services.session_manager import session_manager
from ..utils.security import validate_uuid

router = APIRouter()


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """Get session info including file info and available data types."""
    if not validate_uuid(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format.")

    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    file_info = FileInfo(
        original_filename=session.original_filename,
        file_size=session.file_size,
        xaf_version=session.xaf_version,
        fiscal_year=session.parsed_data.get("header", [{}])[0].get("fiscalYear", ""),
        company_name=session.parsed_data.get("company", [{}])[0].get("companyName", ""),
        currency=session.parsed_data.get("header", [{}])[0].get("curCode", ""),
        start_date=session.parsed_data.get("header", [{}])[0].get("startDate", ""),
        end_date=session.parsed_data.get("header", [{}])[0].get("endDate", ""),
        date_created=session.parsed_data.get("header", [{}])[0].get("dateCreated", ""),
        software=session.parsed_data.get("header", [{}])[0].get("softwareDesc", ""),
    )

    counts = get_record_counts(session.parsed_data)
    data_types = [
        DataTypeInfo(
            name=key,
            display_name=DATA_TYPE_DISPLAY.get(key, key),
            record_count=counts.get(key, 0),
        )
        for key in session.parsed_data
    ]

    from datetime import datetime, timezone
    created_str = datetime.fromtimestamp(session.created_at, tz=timezone.utc).isoformat()

    return SessionResponse(
        session_id=session.session_id,
        file_info=file_info,
        data_types=data_types,
        created_at=created_str,
    )


@router.post("/restart", response_model=RestartResponse)
async def restart(body: RestartRequest) -> RestartResponse:
    """Clear session and delete all temp files."""
    if not validate_uuid(body.session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format.")

    destroyed = session_manager.destroy_session(body.session_id)
    if not destroyed:
        raise HTTPException(status_code=404, detail="Session not found.")

    return RestartResponse(status="ok", message="Session cleared successfully.")
