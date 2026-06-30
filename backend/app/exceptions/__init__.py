"""Hierarchical exception hierarchy for the application.

Every layer catches only what it should. Global FastAPI exception middleware
translates these into consistent HTTP error responses.
"""

from typing import Any, Optional


class BaseApplicationException(Exception):
    """Root exception for all application errors.

    Attributes:
        message: Human-readable error description.
        details: Optional structured data about the error.
        status_code: Suggested HTTP status code (used by middleware).
    """

    status_code: int = 500

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# --- Parsing Layer ---


class ParsingException(BaseApplicationException):
    """Raised when a source document cannot be parsed."""

    status_code = 422


class UnsupportedFormatException(ParsingException):
    """Raised when the file format is not supported."""

    status_code = 415


# --- Extraction Layer ---


class ExtractionException(BaseApplicationException):
    """Raised when structured data cannot be extracted from parsed content."""

    status_code = 422


# --- Normalization Layer ---


class NormalizationException(BaseApplicationException):
    """Raised when a field value cannot be normalized."""

    status_code = 422


# --- Fusion Layer ---


class FusionException(BaseApplicationException):
    """Raised when candidate data fusion fails."""

    status_code = 500


# --- Projection Layer ---


class ProjectionException(BaseApplicationException):
    """Raised when a projection configuration is invalid or fails."""

    status_code = 400


# --- Validation Layer ---


class ValidationException(BaseApplicationException):
    """Raised when the final canonical profile fails schema validation."""

    status_code = 422


# --- Repository / Database Layer ---


class RepositoryException(BaseApplicationException):
    """Raised for data-access errors."""

    status_code = 500


class DatabaseException(RepositoryException):
    """Raised for low-level database connectivity / query errors."""

    status_code = 503


class EntityNotFoundException(RepositoryException):
    """Raised when a requested entity does not exist."""

    status_code = 404


# --- API Layer ---


class APIException(BaseApplicationException):
    """Raised for request-level errors surfaced to the client."""

    status_code = 400


class FileUploadException(APIException):
    """Raised when file upload validation fails."""

    status_code = 400
