"""Domain enumerations used across the application."""

from enum import Enum


class SourceType(str, Enum):
    """Types of candidate data sources."""

    RESUME = "resume"
    RECRUITER_CSV = "recruiter_csv"
    RECRUITER_NOTES = "recruiter_notes"


class FieldName(str, Enum):
    """Canonical field names in the candidate profile.

    Using an enum prevents typos and provides a single source of truth
    for all fields that flow through the pipeline.
    """

    FULL_NAME = "full_name"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    EMAIL = "email"
    PHONE = "phone"
    LOCATION = "location"
    CURRENT_TITLE = "current_title"
    CURRENT_COMPANY = "current_company"
    SUMMARY = "summary"
    SKILLS = "skills"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    GITHUB_URL = "github_url"
    LINKEDIN_URL = "linkedin_url"
    PORTFOLIO_URL = "portfolio_url"
    YEARS_OF_EXPERIENCE = "years_of_experience"
    LANGUAGES = "languages"
    CERTIFICATIONS = "certifications"


class TransformationStatus(str, Enum):
    """Status of a transformation run."""

    PENDING = "pending"
    PARSING = "parsing"
    EXTRACTING = "extracting"
    NORMALIZING = "normalizing"
    FUSING = "fusing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConfidenceLevel(str, Enum):
    """Qualitative confidence levels derived from numeric scores."""

    HIGH = "high"  # >= 0.8
    MEDIUM = "medium"  # >= 0.5
    LOW = "low"  # >= 0.2
    VERY_LOW = "very_low"  # < 0.2

    @classmethod
    def from_score(cls, score: float) -> "ConfidenceLevel":
        """Convert a numeric confidence score to a qualitative level."""
        if score >= 0.8:
            return cls.HIGH
        if score >= 0.5:
            return cls.MEDIUM
        if score >= 0.2:
            return cls.LOW
        return cls.VERY_LOW
