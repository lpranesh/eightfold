"""Request DTOs."""

from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class ProjectionConfigDTO(BaseModel):
    """Configuration for projecting the canonical profile."""
    include_fields: Optional[list[str]] = None
    exclude_fields: Optional[list[str]] = None
    rename_fields: dict[str, str] = Field(default_factory=dict)
    hide_metadata: bool = False
    include_provenance: bool = True
    include_confidence: bool = True


class TransformRequest(BaseModel):
    """Request payload for transformation."""
    github_url: Optional[HttpUrl] = None
    linkedin_url: Optional[HttpUrl] = None
    projection: Optional[ProjectionConfigDTO] = None
