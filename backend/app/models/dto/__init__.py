"""Data Transfer Objects for API request/response models.

DTOs are separate from domain models to decouple the API contract
from internal representations.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.domain.enums import SourceType


# --- Request DTOs ---

class SourceUpload(BaseModel):
    """Metadata for a single uploaded source file."""

    source_type: SourceType
    filename: str


class TransformRequest(BaseModel):
    """Request body for the transform endpoint.

    Sources are uploaded as multipart form data; this model carries
    the metadata for each source.
    """

    sources: list[SourceUpload] = Field(
        ..., min_length=1, description="At least one source is required"
    )


# --- Response DTOs ---

class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str
    detail: Optional[str] = None
    status_code: int


class TransformResponse(BaseModel):
    """Response from the transform endpoint."""

    candidate_id: str
    profile: dict[str, Any]
    metadata: dict[str, Any]
    sources_processed: list[str]
    overall_confidence: float
    overall_confidence_level: str
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime


class CandidateListItem(BaseModel):
    """Summary of a candidate for list views."""

    id: str
    full_name: Optional[str]
    email: Optional[str]
    current_title: Optional[str]
    sources_count: int
    overall_confidence: float
    created_at: datetime


class CandidateListResponse(BaseModel):
    """Paginated list of candidates."""

    candidates: list[CandidateListItem]
    total: int
    limit: int
    offset: int


class CandidateDetailResponse(BaseModel):
    """Full candidate detail response."""

    id: str
    profile: dict[str, Any]
    metadata: dict[str, Any]
    provenance: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str
    timestamp: datetime
