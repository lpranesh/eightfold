"""Extractor interface definition."""

from abc import ABC, abstractmethod
from app.models.intermediate import ExtractedCandidate, ParsedDocument, SourceType


class ExtractorInterface(ABC):
    """Abstract base class for field extractors."""

    @abstractmethod
    def supported_source_types(self) -> list[SourceType]:
        """Return the source types this extractor supports."""

    @abstractmethod
    def extract(self, parsed: ParsedDocument) -> ExtractedCandidate:
        """Extract structured fields from parsed content."""
