"""Domain models for the canonical candidate profile.

The CanonicalProfile is the final, validated output of the transformation
pipeline. Every field carries provenance and confidence metadata.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.domain.enums import ConfidenceLevel, FieldName, SourceType


class FieldProvenance(BaseModel):
    """Provenance record for a single field in the canonical profile.

    Records which source was selected, what alternatives existed,
    why the selection was made, and what normalizations were applied.
    """

    field_name: FieldName
    selected_source: SourceType
    selected_value: Any
    competing_values: list[dict[str, Any]] = Field(default_factory=list)
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    normalizations_applied: list[str] = Field(default_factory=list)
    agreeing_sources: int = 0
    total_sources: int = 0


class ExperienceEntry(BaseModel):
    """A single work experience entry."""

    title: Optional[str] = None
    company: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    is_current: bool = False


class EducationEntry(BaseModel):
    """A single education entry."""

    degree: Optional[str] = None
    institution: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None


class CanonicalProfile(BaseModel):
    """The canonical, unified candidate profile.

    This is the single source of truth produced by the transformation
    pipeline. Every field is optional because we prefer honest gaps
    over fabricated data.
    """

    # --- Identity ---
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

    # --- Professional ---
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    summary: Optional[str] = None
    years_of_experience: Optional[float] = None

    # --- Collections ---
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)

    # --- Links ---
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class CandidateMetadata(BaseModel):
    """Metadata about the transformation that produced this profile."""

    transformation_run_id: str
    sources_processed: list[SourceType] = Field(default_factory=list)
    total_fields_extracted: int = 0
    total_conflicts_resolved: int = 0
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    processing_duration_ms: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    warnings: list[str] = Field(default_factory=list)


class CandidateRecord(BaseModel):
    """Complete candidate record: profile + metadata + provenance.

    This is the top-level domain object stored and returned by the system.
    """

    id: Optional[str] = None
    profile: CanonicalProfile
    metadata: CandidateMetadata
    provenance: dict[str, FieldProvenance] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
