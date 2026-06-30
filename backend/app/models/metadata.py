"""Metadata models for the transformation process."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel

from app.models.intermediate import SourceType


class ConfidenceLevel(str, Enum):
    """Overall confidence level categories."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    @classmethod
    def from_score(cls, score: float) -> "ConfidenceLevel":
        if score >= 0.8:
            return cls.HIGH
        elif score >= 0.5:
            return cls.MEDIUM
        return cls.LOW


class FieldProvenance(BaseModel):
    """Detailed provenance for a single canonical field."""
    field_name: str
    selected_value: Any
    selected_source: str
    confidence: float
    confidence_level: ConfidenceLevel
    competing_values: list[dict[str, Any]]
    reason: str
    normalizations_applied: list[str]


class CandidateMetadata(BaseModel):
    """Metadata about the transformation run."""
    sources_processed: list[SourceType]
    total_fields_extracted: int
    total_conflicts_resolved: int
    overall_confidence: float
    overall_confidence_level: ConfidenceLevel
    processing_duration_ms: float
    warnings: list[str] = []
