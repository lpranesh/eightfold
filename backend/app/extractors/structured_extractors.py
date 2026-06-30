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

_GITHUB_FIELD_MAP: dict[str, FieldName] = {
    "name": FieldName.FULL_NAME, "login": FieldName.GITHUB_URL,
    "email": FieldName.EMAIL, "bio": FieldName.SUMMARY,
    "location": FieldName.LOCATION, "company": FieldName.CURRENT_COMPANY,
    "html_url": FieldName.GITHUB_URL, "blog": FieldName.PORTFOLIO_URL,
}

_LINKEDIN_FIELD_MAP: dict[str, FieldName] = {
    "full_name": FieldName.FULL_NAME, "first_name": FieldName.FIRST_NAME,
    "last_name": FieldName.LAST_NAME, "email": FieldName.EMAIL,
    "headline": FieldName.CURRENT_TITLE, "location": FieldName.LOCATION,
    "summary": FieldName.SUMMARY, "skills": FieldName.SKILLS,
    "experience": FieldName.EXPERIENCE, "education": FieldName.EDUCATION,
    "public_profile_url": FieldName.LINKEDIN_URL, "profile_url": FieldName.LINKEDIN_URL,
    "certifications": FieldName.CERTIFICATIONS, "languages": FieldName.LANGUAGES,
}


def _extract_mapped(data: dict[str, Any], field_map: dict[str, FieldName],
                     source_type: SourceType) -> list[ExtractedValue]:
    """Extract values from a dict using a field mapping."""
    values: list[ExtractedValue] = []
    for key, field_name in field_map.items():
        val = data.get(key)
        if val is None or val == "" or val == []:
            continue
        # For github login, convert to URL
        if key == "login" and field_name == FieldName.GITHUB_URL:
            val = f"https://github.com/{val}"
        values.append(ExtractedValue(
            field_name=field_name, raw_value=val, source_type=source_type,
            extraction_method="field_mapping", extraction_confidence=0.90,
            source_location=f"field:{key}",
        ))
    return values


class ATSExtractor(ExtractorInterface):
    """Extractor for ATS JSON data."""

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.ATS_JSON]

    def extract(self, parsed: ParsedContent) -> ExtractedRecord:
        data = parsed.structured_data or {}
        values = _extract_mapped(data, _ATS_FIELD_MAP, SourceType.ATS_JSON)
        return ExtractedRecord(source_type=SourceType.ATS_JSON, values=values)


class GitHubExtractor(ExtractorInterface):
    """Extractor for GitHub profile JSON."""

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.GITHUB]

    def extract(self, parsed: ParsedContent) -> ExtractedRecord:
        data = parsed.structured_data or {}
        values = _extract_mapped(data, _GITHUB_FIELD_MAP, SourceType.GITHUB)
        # Extract top languages if present
        repos = data.get("repos", data.get("repositories", []))
        if isinstance(repos, list):
            langs = set()
            for repo in repos:
                if isinstance(repo, dict) and repo.get("language"):
                    langs.add(repo["language"])
            if langs:
                values.append(ExtractedValue(
                    field_name=FieldName.SKILLS, raw_value=list(langs),
                    source_type=SourceType.GITHUB, extraction_method="repo_analysis",
                    extraction_confidence=0.70,
                ))
        return ExtractedRecord(source_type=SourceType.GITHUB, values=values)


class LinkedInExtractor(ExtractorInterface):
    """Extractor for LinkedIn profile JSON."""

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.LINKEDIN]

    def extract(self, parsed: ParsedContent) -> ExtractedRecord:
        data = parsed.structured_data or {}
        values = _extract_mapped(data, _LINKEDIN_FIELD_MAP, SourceType.LINKEDIN)
        return ExtractedRecord(source_type=SourceType.LINKEDIN, values=values)


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
