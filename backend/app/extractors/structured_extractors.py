"""Structured data extractors for JSON and CSV sources."""

import logging
from typing import Any, Optional

from app.interfaces import ExtractorInterface
from app.models.domain.enums import FieldName, SourceType
from app.models.domain.source import ExtractedRecord, ExtractedValue, ParsedContent

logger = logging.getLogger(__name__)

# Field mappings for each source type
_ATS_FIELD_MAP: dict[str, FieldName] = {
    "name": FieldName.FULL_NAME, "full_name": FieldName.FULL_NAME,
    "first_name": FieldName.FIRST_NAME, "last_name": FieldName.LAST_NAME,
    "email": FieldName.EMAIL, "email_address": FieldName.EMAIL,
    "phone": FieldName.PHONE, "phone_number": FieldName.PHONE,
    "location": FieldName.LOCATION, "city": FieldName.LOCATION,
    "title": FieldName.CURRENT_TITLE, "current_title": FieldName.CURRENT_TITLE,
    "job_title": FieldName.CURRENT_TITLE, "position": FieldName.CURRENT_TITLE,
    "company": FieldName.CURRENT_COMPANY, "current_company": FieldName.CURRENT_COMPANY,
    "summary": FieldName.SUMMARY, "skills": FieldName.SKILLS,
    "experience": FieldName.EXPERIENCE, "education": FieldName.EDUCATION,
    "years_of_experience": FieldName.YEARS_OF_EXPERIENCE,
    "linkedin": FieldName.LINKEDIN_URL, "linkedin_url": FieldName.LINKEDIN_URL,
    "github": FieldName.GITHUB_URL, "github_url": FieldName.GITHUB_URL,
}

def _extract_mapped(data: dict[str, Any], field_map: dict[str, FieldName],
                     source_type: SourceType) -> list[ExtractedValue]:
    """Extract values from a dict using a field mapping."""
    values: list[ExtractedValue] = []
    for key, field_name in field_map.items():
        val = data.get(key)
        if val is None or val == "" or val == []:
            continue
        values.append(ExtractedValue(
            field_name=field_name, raw_value=val, source_type=source_type,
            extraction_method="field_mapping", extraction_confidence=0.90,
            source_location=f"field:{key}",
        ))
    return values


class CSVExtractor(ExtractorInterface):
    """Extractor for recruiter CSV data."""

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.RECRUITER_CSV]

    def extract(self, parsed: ParsedContent) -> ExtractedRecord:
        data = parsed.structured_data or {}
        rows = data.get("rows", [])
        if not rows:
            return ExtractedRecord(source_type=SourceType.RECRUITER_CSV,
                                   extraction_warnings=["No data rows in CSV"])
        # Use the first row
        row = rows[0]
        values = _extract_mapped(row, _ATS_FIELD_MAP, SourceType.RECRUITER_CSV)
        return ExtractedRecord(source_type=SourceType.RECRUITER_CSV, values=values)


class RecruiterNotesExtractor(ExtractorInterface):
    """Extractor for plain text recruiter notes."""

    import re
    EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
    PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    YOE_RE = re.compile(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)", re.I)

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.RECRUITER_NOTES]

    def extract(self, parsed: ParsedContent) -> ExtractedRecord:
        text = parsed.raw_text or ""
        values: list[ExtractedValue] = []
        st = SourceType.RECRUITER_NOTES

        emails = self.EMAIL_RE.findall(text)
        if emails:
            values.append(ExtractedValue(field_name=FieldName.EMAIL, raw_value=emails[0].lower(),
                source_type=st, extraction_method="regex", extraction_confidence=0.80))

        phones = self.PHONE_RE.findall(text)
        if phones:
            values.append(ExtractedValue(field_name=FieldName.PHONE, raw_value=phones[0],
                source_type=st, extraction_method="regex", extraction_confidence=0.70))

        yoe = self.YOE_RE.search(text)
        if yoe:
            values.append(ExtractedValue(field_name=FieldName.YEARS_OF_EXPERIENCE,
                raw_value=float(yoe.group(1)), source_type=st,
                extraction_method="regex", extraction_confidence=0.75))

        if text:
            values.append(ExtractedValue(field_name=FieldName.SUMMARY, raw_value=text[:500],
                source_type=st, extraction_method="full_text", extraction_confidence=0.40))

        return ExtractedRecord(source_type=st, values=values)
