"""Domain models representing the final canonical profile."""

from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field
from app.models.intermediate import SourceType

T = TypeVar('T')

class CanonicalField(BaseModel, Generic[T]):
    """A single field with its value, confidence, and origin sources."""
    value: T
    field_type: Optional[str] = None
    confidence: float = 0.0
    sources: list[SourceType] = Field(default_factory=list)


class EducationEntry(BaseModel):
    """A single education record."""
    institution: str
    degree: Optional[str] = None
    graduation_year: Optional[int] = None


class ExperienceEntry(BaseModel):
    """A single professional experience record."""
    company: str
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False


class CanonicalProfile(BaseModel):
    """The unified, canonical representation of a candidate."""
    model_config = ConfigDict(extra="ignore")

    full_name: Optional[CanonicalField[str]] = None
    first_name: Optional[CanonicalField[str]] = None
    last_name: Optional[CanonicalField[str]] = None
    emails: list[CanonicalField[str]] = Field(default_factory=list)
    phones: list[CanonicalField[str]] = Field(default_factory=list)
    location: Optional[CanonicalField[str]] = None
    
    current_title: Optional[CanonicalField[str]] = None
    current_company: Optional[CanonicalField[str]] = None
    years_of_experience: Optional[CanonicalField[float]] = None
    
    education: list[CanonicalField[EducationEntry]] = Field(default_factory=list)
    experience: list[CanonicalField[ExperienceEntry]] = Field(default_factory=list)
    skills: list[CanonicalField[str]] = Field(default_factory=list)
    certifications: list[CanonicalField[str]] = Field(default_factory=list)
    languages: list[CanonicalField[str]] = Field(default_factory=list)
    
    summary: Optional[CanonicalField[str]] = None
    linkedin_url: Optional[CanonicalField[str]] = None
    github_url: Optional[CanonicalField[str]] = None
    portfolio_url: Optional[CanonicalField[str]] = None
