"""Field normalizers for cleaning and standardizing extracted values."""

import logging
import re
from typing import Optional

from app.interfaces import NormalizerInterface
from app.models.domain.enums import FieldName, SourceType
from app.models.domain.source import ExtractedValue

logger = logging.getLogger(__name__)


class NameNormalizer(NormalizerInterface):
    """Normalize name fields to title case, strip excess whitespace."""

    def supported_fields(self) -> list[FieldName]:
        return [FieldName.FULL_NAME, FieldName.FIRST_NAME, FieldName.LAST_NAME]

    def normalize(self, value: ExtractedValue) -> ExtractedValue:
        raw = str(value.raw_value).strip()
        # Remove extra whitespace
        cleaned = re.sub(r"\s+", " ", raw)
        # Title case, but preserve particles like "de", "van", "von"
        parts = cleaned.split()
        particles = {"de", "del", "van", "von", "der", "la", "le", "di"}
        normalized = []
        for i, part in enumerate(parts):
            if part.lower() in particles and i > 0:
                normalized.append(part.lower())
            else:
                normalized.append(part.capitalize())
        result = " ".join(normalized)
        return ExtractedValue(
            field_name=value.field_name, raw_value=result,
            source_type=value.source_type, extraction_method=value.extraction_method,
            extraction_confidence=value.extraction_confidence,
            source_location=value.source_location,
        )


class EmailNormalizer(NormalizerInterface):
    """Normalize email to lowercase, strip whitespace."""

    def supported_fields(self) -> list[FieldName]:
        return [FieldName.EMAIL]

    def normalize(self, value: ExtractedValue) -> ExtractedValue:
        raw = str(value.raw_value).strip().lower()
        return ExtractedValue(
            field_name=value.field_name, raw_value=raw,
            source_type=value.source_type, extraction_method=value.extraction_method,
            extraction_confidence=value.extraction_confidence,
            source_location=value.source_location,
        )


class PhoneNormalizer(NormalizerInterface):
    """Normalize phone numbers to a consistent format."""

    def supported_fields(self) -> list[FieldName]:
        return [FieldName.PHONE]

    def normalize(self, value: ExtractedValue) -> ExtractedValue:
        raw = str(value.raw_value)
        digits = re.sub(r"[^\d+]", "", raw)
        # Format US numbers
        if len(digits) == 10:
            formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits.startswith("1"):
            formatted = f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            formatted = digits
        return ExtractedValue(
            field_name=value.field_name, raw_value=formatted,
            source_type=value.source_type, extraction_method=value.extraction_method,
            extraction_confidence=value.extraction_confidence,
            source_location=value.source_location,
        )


class SkillsNormalizer(NormalizerInterface):
    """Normalize skills lists — deduplicate, sort, title case."""

    def supported_fields(self) -> list[FieldName]:
        return [FieldName.SKILLS]

    def normalize(self, value: ExtractedValue) -> ExtractedValue:
        raw = value.raw_value
        if isinstance(raw, str):
            skills = [s.strip() for s in re.split(r"[,;|]", raw) if s.strip()]
        elif isinstance(raw, list):
            skills = [str(s).strip() for s in raw if str(s).strip()]
        else:
            skills = [str(raw)]
        # Deduplicate case-insensitively while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for s in skills:
            key = s.lower()
            if key not in seen:
                seen.add(key)
                unique.append(s)
        return ExtractedValue(
            field_name=value.field_name, raw_value=sorted(unique),
            source_type=value.source_type, extraction_method=value.extraction_method,
            extraction_confidence=value.extraction_confidence,
            source_location=value.source_location,
        )


class URLNormalizer(NormalizerInterface):
    """Normalize URLs — ensure https prefix, strip trailing slashes."""

    def supported_fields(self) -> list[FieldName]:
        return [FieldName.GITHUB_URL, FieldName.LINKEDIN_URL, FieldName.PORTFOLIO_URL]

    def normalize(self, value: ExtractedValue) -> ExtractedValue:
        url = str(value.raw_value).strip().rstrip("/")
        if url and not url.startswith("http"):
            url = "https://" + url
        return ExtractedValue(
            field_name=value.field_name, raw_value=url,
            source_type=value.source_type, extraction_method=value.extraction_method,
            extraction_confidence=value.extraction_confidence,
            source_location=value.source_location,
        )


class LocationNormalizer(NormalizerInterface):
    """Normalize location strings — clean whitespace, title case."""

    def supported_fields(self) -> list[FieldName]:
        return [FieldName.LOCATION]

    def normalize(self, value: ExtractedValue) -> ExtractedValue:
        raw = str(value.raw_value).strip()
        cleaned = re.sub(r"\s+", " ", raw)
        # Title case each part
        parts = [p.strip() for p in cleaned.split(",")]
        normalized = ", ".join(p.title() for p in parts if p)
        return ExtractedValue(
            field_name=value.field_name, raw_value=normalized,
            source_type=value.source_type, extraction_method=value.extraction_method,
            extraction_confidence=value.extraction_confidence,
            source_location=value.source_location,
        )


def get_all_normalizers() -> list[NormalizerInterface]:
    """Return all built-in normalizer instances."""
    return [
        NameNormalizer(),
        EmailNormalizer(),
        PhoneNormalizer(),
        SkillsNormalizer(),
        URLNormalizer(),
        LocationNormalizer(),
    ]
