"""Upload endpoint: receive XAF file, parse, create session."""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from ..models.schemas import DataTypeInfo, FileInfo, UploadResponse, ValidationCheckSchema, ValidationResultSchema
from ..services.data_extractor import DATA_TYPE_DISPLAY, extract_all, get_record_counts
from ..services.session_manager import session_manager
from ..services.validator import validate_xaf
from ..services.xaf_parser import XAFParseError, parse_xaf
from ..utils.security import safe_path, validate_xml_start

logger = logging.getLogger(__name__)

router = APIRouter()

# Limits
MAX_FILE_SIZE = 250 * 1024 * 1024  # 250 MB
PARSE_TIMEOUT = 60  # seconds
ALLOWED_EXTENSIONS = {".xaf", ".xml"}

# Thread pool for CPU-bound parsing
_parse_pool = ThreadPoolExecutor(max_workers=2)


@router.post("/upload", response_model=UploadResponse)
async def upload_file(request: Request, file: UploadFile = File(...)) -> UploadResponse:
    """Upload an XAF file, parse it, and create a session."""
    # R-UP-1: Check Content-Length header
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 250 MB.")

    # R-UP-3: Validate file extension
    original_filename = file.filename or "unknown.xaf"
    _, ext = os.path.splitext(original_filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid file extension '{ext}'. Only .xaf and .xml are accepted.",
        )

    # Read the file content with size limit
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 250 MB.")

    if len(content) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    # R-UP-2: Validate XML declaration
    if not validate_xml_start(content):
        raise HTTPException(
            status_code=422,
            detail="Invalid file: does not start with an XML declaration.",
        )

    # Create session
    session = session_manager.create_session()

    # R-UP-4: Save with UUID-based filename
    safe_filename = f"{uuid.uuid4()}.xaf"
    upload_path = safe_path(session.temp_dir, safe_filename)
    with open(upload_path, "wb") as f:
        f.write(content)

    # Store file info
    session.original_filename = original_filename
    session.file_size = len(content)

    # R-UP-6: Parse with timeout
    try:
        # Send progress via WebSocket if connections exist
        def progress_cb(pct: int, msg: str) -> None:
            # Progress callback - will be used by WebSocket if connected
            pass

        loop = asyncio.get_event_loop()
        audit_file = await asyncio.wait_for(
            loop.run_in_executor(_parse_pool, parse_xaf, content, progress_cb),
            timeout=PARSE_TIMEOUT,
        )
    except asyncio.TimeoutError:
        session_manager.destroy_session(session.session_id)
        raise HTTPException(status_code=422, detail="Parsing timed out (60 second limit).")
    except XAFParseError as exc:
        session_manager.destroy_session(session.session_id)
        raise HTTPException(status_code=422, detail=f"XAF parsing error: {exc}")
    except Exception as exc:
        logger.exception("Unexpected parsing error")
        session_manager.destroy_session(session.session_id)
        raise HTTPException(status_code=500, detail="Internal error during parsing.")

    # Extract flat data for export
    parsed_data = extract_all(audit_file)
    session.parsed_data = parsed_data
    session.xaf_version = audit_file.sourceVersion
    session.fiscal_year = audit_file.header.fiscalYear or ""
    session.company_name = audit_file.company.companyName or ""

    # Run validation and store in session for XLSX export
    vresult = validate_xaf(audit_file)
    session.validation_checks = [
        {"section": c.section, "check": c.check, "declared": c.declared, "computed": c.computed, "passed": c.passed}
        for c in vresult.checks
    ]

    # Build response
    file_info = FileInfo(
        original_filename=original_filename,
        file_size=len(content),
        xaf_version=audit_file.sourceVersion,
        fiscal_year=audit_file.header.fiscalYear,
        company_name=audit_file.company.companyName,
        currency=audit_file.header.curCode,
        start_date=audit_file.header.startDate,
        end_date=audit_file.header.endDate,
        date_created=audit_file.header.dateCreated,
        software=f"{audit_file.header.softwareDesc} {audit_file.header.softwareVersion}",
    )

    counts = get_record_counts(parsed_data)
    data_types = [
        DataTypeInfo(
            name=key,
            display_name=DATA_TYPE_DISPLAY.get(key, key),
            record_count=counts.get(key, 0),
        )
        for key in parsed_data
    ]

    # Build validation response from stored checks
    passed_count = sum(1 for c in session.validation_checks if c["passed"])
    total_count = len(session.validation_checks)
    validation = ValidationResultSchema(
        checks=[
            ValidationCheckSchema(**c)
            for c in session.validation_checks
        ],
        all_passed=passed_count == total_count,
        summary=f"{passed_count}/{total_count} checks passed",
    )

    return UploadResponse(
        session_id=session.session_id,
        file_info=file_info,
        data_types=data_types,
        validation=validation,
    )
