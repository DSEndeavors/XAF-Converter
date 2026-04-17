"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Any


# --- Request schemas ---

class PreviewRequest(BaseModel):
    session_id: str
    data_types: list[str]
    search: Optional[str] = None
    page: int = 1
    page_size: int = 50


class ExportRequest(BaseModel):
    session_id: str
    data_types: list[str]
    format: str = Field(..., pattern=r"^(csv|xlsx|json|parquet)$")


class RestartRequest(BaseModel):
    session_id: str


# --- Response schemas ---

class FileInfo(BaseModel):
    original_filename: str
    file_size: int
    xaf_version: str
    fiscal_year: str
    company_name: str
    currency: str
    start_date: str
    end_date: str
    date_created: str
    software: str


class DataTypeInfo(BaseModel):
    name: str
    display_name: str
    record_count: int


class ValidationCheckSchema(BaseModel):
    section: str
    check: str
    declared: str
    computed: str
    passed: bool


class ValidationResultSchema(BaseModel):
    checks: list[ValidationCheckSchema]
    all_passed: bool
    summary: str


class UploadResponse(BaseModel):
    session_id: str
    file_info: FileInfo
    data_types: list[DataTypeInfo]
    validation: ValidationResultSchema


class SessionResponse(BaseModel):
    session_id: str
    file_info: FileInfo
    data_types: list[DataTypeInfo]
    created_at: str


class PreviewData(BaseModel):
    data_type: str
    columns: list[str]
    rows: list[dict[str, Any]]
    total_count: int


class PreviewResponse(BaseModel):
    session_id: str
    previews: list[PreviewData]


class ExportResponse(BaseModel):
    session_id: str
    filename: str
    download_url: str
    format: str
    data_types: list[str]


class RestartResponse(BaseModel):
    status: str = "ok"
    message: str = "Session cleared"


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class ErrorResponse(BaseModel):
    detail: str


class ProgressMessage(BaseModel):
    """WebSocket progress update."""
    session_id: str
    stage: str  # "parsing", "exporting"
    percentage: int  # 0-100
    message: str
