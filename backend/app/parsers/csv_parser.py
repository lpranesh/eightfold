"""CSV parser for recruiter spreadsheet data.

Converts CSV rows into structured data suitable for extraction.
"""

import csv
import io
import logging
from typing import Any

from app.exceptions import ParsingException
from app.interfaces import ParserInterface
from app.models.domain.enums import SourceType
from app.models.domain.source import ParsedContent

logger = logging.getLogger(__name__)


class CSVParser(ParserInterface):
    """Parser for recruiter CSV files.

    Reads the CSV into a list of dictionaries (one per row).
    For single-candidate CSVs, the first data row is the candidate.
    For multi-candidate CSVs, all rows are returned.
    """

    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        """Check if this parser handles the given source."""
        return file_extension.lower() == ".csv"

    def parse(self, content: bytes, source_type: SourceType) -> ParsedContent:
        """Parse a CSV file into structured data.

        Args:
            content: Raw CSV bytes.
            source_type: The source type (typically RECRUITER_CSV).

        Returns:
            ParsedContent with structured_data containing the rows.

        Raises:
            ParsingException: If CSV parsing fails.
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
                    message="Cannot decode CSV file",
                    details={"error": str(exc)},
                )

        try:
            # Sniff the dialect to handle different CSV formats
            sample = text[:8192]
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel  # type: ignore[assignment]
                warnings.append("Could not detect CSV dialect, using default")

            reader = csv.DictReader(io.StringIO(text), dialect=dialect)
            rows: list[dict[str, Any]] = []

            for i, row in enumerate(reader):
                # Clean up keys and values
                cleaned = {
                    k.strip().lower().replace(" ", "_"): v.strip() if v else ""
                    for k, v in row.items()
                    if k is not None
                }
                rows.append(cleaned)

            if not rows:
                warnings.append("CSV file contains no data rows")

            logger.info(
                "CSV parsed successfully",
                extra={"rows": len(rows), "columns": len(rows[0]) if rows else 0},
            )

            return ParsedContent(
                source_type=source_type,
                structured_data={"rows": rows, "row_count": len(rows)},
                raw_text=text,
                parse_warnings=warnings,
                metadata={
                    "parser": "csv",
                    "row_count": len(rows),
                    "columns": list(rows[0].keys()) if rows else [],
                },
            )

        except Exception as exc:
            raise ParsingException(
                message=f"Failed to parse CSV file: {exc}",
                details={"warnings": warnings},
            )
