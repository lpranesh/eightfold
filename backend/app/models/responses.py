"""Response DTOs."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error format."""
    error: str
    detail: Optional[str] = None
    status_code: int


class TransformResponse(BaseModel):
    """Response from transformation pipeline."""
    profile: dict[str, Any]
    metadata: Optional[dict[str, Any]] = None
    provenance: Optional[dict[str, Any]] = None
    warnings: list[str] = Field(default_factory=list)
