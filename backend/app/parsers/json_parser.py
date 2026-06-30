"""JSON parser for ATS, GitHub, and LinkedIn profile data.

Handles JSON files from various structured sources.
"""

import json
import logging
from typing import Any

from app.exceptions import ParsingException
from app.interfaces import ParserInterface
from app.models.domain.enums import SourceType
from app.models.domain.source import ParsedContent

logger = logging.getLogger(__name__)


class JSONParser(ParserInterface):
    """Parser for JSON source files (ATS, GitHub, LinkedIn).

    Validates JSON structure and wraps it in ParsedContent for downstream
    processing by source-specific extractors.
    """

    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        """Check if this parser handles the given source."""
        return file_extension.lower() == ".json"

    def parse(self, content: bytes, source_type: SourceType) -> ParsedContent:
        """Parse a JSON file into structured data.

        Args:
            content: Raw JSON bytes.
            source_type: The source type (ATS_JSON, GITHUB, LINKEDIN).

        Returns:
            ParsedContent with the parsed JSON as structured_data.

        Raises:
            ParsingException: If JSON parsing fails.
        """
        warnings: list[str] = []

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ParsingException(
                message="Cannot decode JSON file as UTF-8",
                details={"error": str(exc)},
            )

        try:
            data: Any = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ParsingException(
                message=f"Invalid JSON: {exc.msg}",
                details={"line": exc.lineno, "column": exc.colno},
            )

        # Validate that the root is a dict or list
        if not isinstance(data, (dict, list)):
            raise ParsingException(
                message="JSON root must be an object or array",
                details={"actual_type": type(data).__name__},
            )

        # Wrap list in a dict for consistent downstream handling
        if isinstance(data, list):
            data = {"items": data}
            warnings.append("JSON root was an array; wrapped in {items: [...]}")

        logger.info(
            "JSON parsed successfully",
            extra={
                "source_type": source_type.value,
                "keys": list(data.keys()) if isinstance(data, dict) else "N/A",
            },
        )

        return ParsedContent(
            source_type=source_type,
            structured_data=data,
            raw_text=text,
            parse_warnings=warnings,
            metadata={"parser": "json", "source_type": source_type.value},
        )
