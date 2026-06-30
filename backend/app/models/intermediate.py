"""Intermediate data structures used during transformation."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel


class SourceType(str, Enum):
    """Supported input source types."""
    RESUME_PDF = "resume_pdf"
    GITHUB_PROFILE = "github_profile"
    LINKEDIN_PROFILE = "linkedin_profile"
    RECRUITER_CSV = "recruiter_csv"


class ParsedContent(BaseModel):
    """Raw parsed content from a source document."""
    source_type: SourceType
    filename: Optional[str] = None
    raw_text: Optional[str] = None
    structured_data: Optional[dict[str, Any]] = None
    parse_warnings: list[str] = []


class ExtractedValue(BaseModel):
    """A single piece of data extracted from a source."""
    field_name: str
    raw_value: Any
    source_type: SourceType
    extraction_method: str
    extraction_confidence: float = 1.0


class ExtractedRecord(BaseModel):
    """All values extracted from a single source."""
    source_type: SourceType
    values: list[ExtractedValue]
    extraction_warnings: list[str] = []
