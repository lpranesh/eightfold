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


class ProjectionRequest(BaseModel):
    """Request body for the projection endpoint."""

    include_fields: Optional[list[str]] = None
    exclude_fields: Optional[list[str]] = None
    rename_fields: dict[str, str] = Field(default_factory=dict)
    hide_metadata: bool = False


# --- Response DTOs ---


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str
    detail: Optional[str] = None
    status_code: int


class FieldExplanation(BaseModel):
    """Explanation for how a single field was determined."""

    field_name: str
    selected_value: Any
    selected_source: str
    confidence: float
    confidence_level: str
    competing_values: list[dict[str, Any]]
    reason: str
    normalizations_applied: list[str]
    agreeing_sources: int
    total_sources: int


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


class ProjectionResponse(BaseModel):
    """Response from the projection endpoint."""

    candidate_id: str
    projected_profile: dict[str, Any]
    projection_config: dict[str, Any]


class MetadataResponse(BaseModel):
    """Response for candidate metadata."""

    candidate_id: str
    metadata: dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str
    timestamp: datetime


class PipelineStageInfo(BaseModel):
    """Information about a single pipeline stage."""

    name: str
    status: str
    duration_ms: Optional[float] = None
    items_processed: int = 0
    warnings: list[str] = Field(default_factory=list)


class TransformationRunResponse(BaseModel):
    """Detailed information about a transformation run."""

    run_id: str
    candidate_id: str
    stages: list[PipelineStageInfo]
    total_duration_ms: float
    status: str
    created_at: datetime
