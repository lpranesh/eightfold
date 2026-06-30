"""Domain models for source documents and extracted values.

These models represent the intermediate state of data as it flows through
the transformation pipeline — after parsing but before fusion.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.domain.enums import FieldName, SourceType


class ParsedContent(BaseModel):
    """Raw content extracted by a parser from a source document.

    This is the output of the Parser stage and input to the Extractor stage.
    """

    source_type: SourceType
    raw_text: Optional[str] = None
    structured_data: Optional[dict[str, Any]] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    page_count: Optional[int] = None
    parse_warnings: list[str] = Field(default_factory=list)


class ExtractedValue(BaseModel):
    """A single field value extracted from a source.

    Carries provenance information about where the value came from
    and how confident the extraction is.
    """

    field_name: FieldName
    raw_value: Any
    source_type: SourceType
    extraction_method: str = "rule_based"
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_location: Optional[str] = None  # e.g., "page 1, line 5"


class ExtractedRecord(BaseModel):
    """All values extracted from a single source document.

    Groups extracted values by source, preserving the relationship
    between values and their origin.
    """

    source_type: SourceType
    values: list[ExtractedValue] = Field(default_factory=list)
    extraction_warnings: list[str] = Field(default_factory=list)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

    def get_values_for_field(self, field_name: FieldName) -> list[ExtractedValue]:
        """Return all extracted values for a given field name."""
        return [v for v in self.values if v.field_name == field_name]
