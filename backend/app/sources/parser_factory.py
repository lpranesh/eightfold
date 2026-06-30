"""Parser factory for resolving appropriate parsers."""

from app.interfaces.parser import ParserInterface
from app.models.intermediate import SourceType
from app.sources.csv_parser import CSVParser
from app.sources.github_parser import GitHubParser
from app.sources.linkedin_parser import LinkedInParser
from app.sources.pdf_parser import PDFParser
from app.core.exceptions import ParsingException


class ParserFactory:
    """Factory to retrieve the correct parser based on source type/extension."""

    def __init__(self):
        self._parsers: list[ParserInterface] = [
            PDFParser(),
            CSVParser(),
            GitHubParser(),
            LinkedInParser(),
        ]

    def get_parser(self, source_type: SourceType, file_extension: str) -> ParserInterface:
        """Find the first matching parser."""
        for parser in self._parsers:
            if parser.can_parse(source_type, file_extension):
                return parser
        raise ParsingException(
            f"No suitable parser found for {source_type.value} / {file_extension}"
        )
