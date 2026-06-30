"""Domain models representing the final canonical profile."""

from typing import Optional
from pydantic import BaseModel, ConfigDict


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

    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    years_of_experience: Optional[float] = None
    
    education: list[EducationEntry] = []
    experience: list[ExperienceEntry] = []
    skills: list[str] = []
    certifications: list[str] = []
    languages: list[str] = []
    
    summary: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
