"""GitHub JSON Parser."""

import json
from app.interfaces.parser import ParserInterface
from app.models.intermediate import ParsedContent, SourceType
from app.core.exceptions import ParsingException


class GitHubParser(ParserInterface):
    """Parses JSON data returned by the GitHub connector."""

    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        return source_type == SourceType.GITHUB_PROFILE

    def parse(self, content: bytes, source_type: SourceType, filename: str) -> ParsedContent:
        try:
            data = json.loads(content.decode("utf-8"))
            return ParsedContent(
                source_type=source_type,
                filename=filename,
                structured_data=data,
            )
        except Exception as e:
            raise ParsingException(f"Failed to parse GitHub JSON: {e}")
