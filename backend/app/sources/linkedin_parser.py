"""LinkedIn JSON Parser."""

import json
from app.interfaces.parser import ParserInterface
from app.models.intermediate import ParsedContent, SourceType
from app.core.exceptions import ParsingException


class LinkedInParser(ParserInterface):
    """Parses JSON data returned by the LinkedIn connector."""

    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        return source_type == SourceType.LINKEDIN_PROFILE

    def parse(self, content: bytes, source_type: SourceType, filename: str) -> ParsedContent:
        try:
            data = json.loads(content.decode("utf-8"))
            return ParsedContent(
                source_type=source_type,
                filename=filename,
                structured_data=data,
            )
        except Exception as e:
            raise ParsingException(f"Failed to parse LinkedIn JSON: {e}")
