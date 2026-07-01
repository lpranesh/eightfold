"""Plain text parser for recruiter notes.

Simple parser that handles .txt files containing free-form recruiter notes.
"""

import logging

from app.exceptions import ParsingException
from app.interfaces import ParserInterface
from app.models.domain.enums import SourceType
from app.models.domain.source import ParsedDocument

logger = logging.getLogger(__name__)


class TextParser(ParserInterface):
    """Parser for plain text files (recruiter notes).

    Decodes text and performs basic cleanup (whitespace normalization).
    """

    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        """Check if this parser handles the given source."""
        return file_extension.lower() == ".txt"

    def parse(self, content: bytes, source_type: SourceType) -> ParsedDocument:
        """Parse a plain text file.

        Args:
            content: Raw text bytes.
            source_type: The source type (typically RECRUITER_NOTES).

        Returns:
            ParsedDocument with raw_text.

        Raises:
            ParsingException: If the file cannot be decoded.
        """
        warnings: list[str] = []

        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
                warnings.append("File decoded using latin-1 fallback encoding")
            except UnicodeDecodeError as exc:
                raise ParsingException(
                    message="Cannot decode text file",
                    details={"error": str(exc)},
                )

        # Basic cleanup
        text = text.strip()

        if not text:
            warnings.append("Text file is empty")

        logger.info(
            "Text file parsed successfully",
            extra={"text_length": len(text)},
        )

        return ParsedDocument(
            source_type=source_type,
            raw_text=text,
            parse_warnings=warnings,
            metadata={"parser": "text", "char_count": len(text)},
        )
