"""Parser factory — resolves the correct parser for a given source type and file.

Implements the Factory pattern. New parsers can be registered without
modifying existing code (Open/Closed Principle).
"""

import logging
from typing import Optional

from app.exceptions import UnsupportedFormatException
from app.interfaces import ParserInterface
from app.models.domain.enums import SourceType

logger = logging.getLogger(__name__)


class ParserFactory:
    """Factory that selects the appropriate parser for a given input.

    Parsers are registered at construction time. The factory iterates
    registered parsers and asks each if it can handle the input.
    """

    def __init__(self, parsers: Optional[list[ParserInterface]] = None) -> None:
        self._parsers: list[ParserInterface] = parsers or []

    def register(self, parser: ParserInterface) -> None:
        """Register a parser implementation.

        Args:
            parser: A parser that implements ParserInterface.
        """
        self._parsers.append(parser)
        logger.info("Registered parser: %s", type(parser).__name__)

    def get_parser(
        self, source_type: SourceType, file_extension: str
    ) -> ParserInterface:
        """Find a parser that can handle the given source type and extension.

        Args:
            source_type: The type of source document.
            file_extension: File extension (e.g., '.pdf').

        Returns:
            A parser instance.

        Raises:
            UnsupportedFormatException: If no parser can handle the input.
        """
        for parser in self._parsers:
            if parser.can_parse(source_type, file_extension):
                logger.debug(
                    "Selected parser %s for %s (%s)",
                    type(parser).__name__,
                    source_type.value,
                    file_extension,
                )
                return parser

        raise UnsupportedFormatException(
            message=f"No parser available for source_type={source_type.value}, "
            f"extension={file_extension}",
            details={
                "source_type": source_type.value,
                "extension": file_extension,
                "registered_parsers": [type(p).__name__ for p in self._parsers],
            },
        )


def create_default_parser_factory(ocr_enabled: bool = True) -> ParserFactory:
    """Create a ParserFactory with all built-in parsers registered.

    Args:
        ocr_enabled: Whether to enable OCR fallback in the PDF parser.

    Returns:
        A fully configured ParserFactory.
    """
    from app.parsers.csv_parser import CSVParser
    from app.parsers.pdf_parser import PDFParser
    from app.parsers.text_parser import TextParser

    factory = ParserFactory()
    factory.register(PDFParser(ocr_enabled=ocr_enabled))
    factory.register(CSVParser())
    factory.register(TextParser())
    return factory
