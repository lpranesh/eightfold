"""Extractors for structured sources (JSON, CSV)."""

from typing import Any
from app.interfaces.extractor import ExtractorInterface
from app.models.intermediate import ExtractedRecord, ExtractedValue, ParsedContent, SourceType
from app.core.exceptions import ExtractionException


def _extract_mapped(data: dict[str, Any], field_map: dict[str, str], source_type: SourceType) -> list[ExtractedValue]:
    values: list[ExtractedValue] = []
    for key, field_name in field_map.items():
        val = data.get(key)
        if val is None or val == "" or val == []:
            continue
        
        # Github login to URL conversion
        if key == "login" and field_name == "github_url":
            val = f"https://github.com/{val}"
            
        values.append(ExtractedValue(
            field_name=field_name,
            raw_value=val,
            source_type=source_type,
            extraction_method="structured_mapping",
            extraction_confidence=0.95
        ))
    return values


class GitHubStructuredExtractor(ExtractorInterface):
    """Extracts fields from GitHub JSON."""
    
    FIELD_MAP = {
        "name": "full_name", "login": "github_url",
        "email": "email", "bio": "summary",
        "location": "location", "company": "current_company",
        "html_url": "github_url", "blog": "portfolio_url",
    }

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.GITHUB_PROFILE]

    def extract(self, parsed: ParsedContent) -> ExtractedRecord:
        data = parsed.structured_data or {}
        values = _extract_mapped(data, self.FIELD_MAP, SourceType.GITHUB_PROFILE)
        
        repos = data.get("repos", [])
        langs = set()
        for repo in repos:
            if isinstance(repo, dict) and repo.get("language"):
                langs.add(repo["language"])
        if langs:
            values.append(ExtractedValue(
                field_name="skills", raw_value=list(langs),
                source_type=SourceType.GITHUB_PROFILE,
                extraction_method="repo_analysis",
                extraction_confidence=0.8
            ))
            
        return ExtractedRecord(source_type=SourceType.GITHUB_PROFILE, values=values)


class LinkedInStructuredExtractor(ExtractorInterface):
    """Extracts fields from LinkedIn JSON."""

    FIELD_MAP = {
        "full_name": "full_name", "first_name": "first_name",
        "last_name": "last_name", "email": "email",
        "headline": "current_title", "location": "location",
        "summary": "summary", "skills": "skills",
        "public_profile_url": "linkedin_url",
    }

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.LINKEDIN_PROFILE]

    def extract(self, parsed: ParsedContent) -> ExtractedRecord:
        data = parsed.structured_data or {}
        values = _extract_mapped(data, self.FIELD_MAP, SourceType.LINKEDIN_PROFILE)
        return ExtractedRecord(source_type=SourceType.LINKEDIN_PROFILE, values=values)


class CSVStructuredExtractor(ExtractorInterface):
    """Extracts fields from Recruiter CSV."""

    FIELD_MAP = {
        "name": "full_name", "first_name": "first_name", "last_name": "last_name",
        "email": "email", "phone": "phone", "location": "location",
        "title": "current_title", "company": "current_company",
        "years_of_experience": "years_of_experience",
        "linkedin": "linkedin_url", "github": "github_url",
    }

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.RECRUITER_CSV]

    def extract(self, parsed: ParsedContent) -> ExtractedRecord:
        data = parsed.structured_data or {}
        rows = data.get("rows", [])
        if not rows:
            return ExtractedRecord(source_type=SourceType.RECRUITER_CSV, values=[], extraction_warnings=["No data rows in CSV"])
        
        # Use first row
        row = rows[0]
        values = _extract_mapped(row, self.FIELD_MAP, SourceType.RECRUITER_CSV)
        return ExtractedRecord(source_type=SourceType.RECRUITER_CSV, values=values)
