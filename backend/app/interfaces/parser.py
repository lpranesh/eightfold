"""Parser interface definition."""

from abc import ABC, abstractmethod
from app.models.intermediate import ParsedDocument, SourceType


class ParserInterface(ABC):
    """Abstract base class for source parsers."""

    @abstractmethod
    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        """Check if parser supports the given source."""

    @abstractmethod
    def parse(self, content: bytes, source_type: SourceType, filename: str) -> ParsedDocument:
        """Parse raw content into structured intermediate format."""
