"""Domain models — the core business objects of the application."""

from app.models.domain.candidate import (
    CandidateMetadata,
    CandidateRecord,
    CanonicalProfile,
    EducationEntry,
    ExperienceEntry,
    FieldProvenance,
)
from app.models.domain.enums import (
    ConfidenceLevel,
    FieldName,
    SourceType,
    TransformationStatus,
)
from app.models.domain.projection import ProjectionConfig
from app.models.domain.source import ExtractedRecord, ExtractedValue, ParsedContent

__all__ = [
    "CandidateMetadata",
    "CandidateRecord",
    "CanonicalProfile",
    "ConfidenceLevel",
    "EducationEntry",
    "ExperienceEntry",
    "ExtractedRecord",
    "ExtractedValue",
    "FieldName",
    "FieldProvenance",
    "ParsedContent",
    "ProjectionConfig",
    "SourceType",
    "TransformationStatus",
]
