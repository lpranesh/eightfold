"""Recruiter CSV Parser."""

import csv
import io
from app.interfaces.parser import ParserInterface
from app.models.intermediate import ParsedContent, SourceType
from app.core.exceptions import ParsingException


class CSVParser(ParserInterface):
    """Parses recruiter CSV files."""

    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        return source_type == SourceType.RECRUITER_CSV or file_extension == ".csv"

    def parse(self, content: bytes, source_type: SourceType, filename: str) -> ParsedContent:
        try:
            text = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            rows = [row for row in reader]
            
            return ParsedContent(
                source_type=SourceType.RECRUITER_CSV,
                filename=filename,
                structured_data={"rows": rows},
            )
        except Exception as e:
            raise ParsingException(f"Failed to parse CSV: {e}")
