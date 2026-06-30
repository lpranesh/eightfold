"""Regex-based baseline extraction."""

import re
from typing import Any
from app.interfaces.extractor import ExtractorInterface
from app.models.intermediate import ExtractedRecord, ExtractedValue, ParsedContent, SourceType
from app.core.exceptions import ExtractionException


class RegexExtractor(ExtractorInterface):
    """Extracts information using Regular Expressions."""

    EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
    PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    YOE_RE = re.compile(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)", re.I)

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.RESUME_PDF]

    def extract(self, parsed: ParsedContent) -> ExtractedRecord:
        text = parsed.raw_text or ""
        values: list[ExtractedValue] = []
        
        try:
            # Email
            emails = self.EMAIL_RE.findall(text)
            if emails:
                values.append(self._make_val("email", emails[0], parsed.source_type, 0.9))

            # Phone
            phones = self.PHONE_RE.findall(text)
            if phones:
                values.append(self._make_val("phone", phones[0], parsed.source_type, 0.8))

            # YOE
            yoe = self.YOE_RE.search(text)
            if yoe:
                values.append(self._make_val("years_of_experience", float(yoe.group(1)), parsed.source_type, 0.7))

            # Summary (fallback to first block of text)
            if text:
                summary_text = text[:500].strip()
                values.append(self._make_val("summary", summary_text, parsed.source_type, 0.4))

            return ExtractedRecord(source_type=parsed.source_type, values=values)
        except Exception as e:
            raise ExtractionException(f"Regex extraction failed: {e}")

    def _make_val(self, name: str, val: Any, st: SourceType, conf: float) -> ExtractedValue:
        return ExtractedValue(
            field_name=name,
            raw_value=val,
            source_type=st,
            extraction_method="regex",
            extraction_confidence=conf
        )
