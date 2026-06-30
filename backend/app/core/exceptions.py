"""Hierarchical custom exceptions for the application."""


class ApplicationException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ValidationException(ApplicationException):
    """Raised when input validation fails."""


class TransformationException(ApplicationException):
    """Base exception for pipeline transformation errors."""


class ParsingException(TransformationException):
    """Raised when source parsing fails."""


class ExtractionException(TransformationException):
    """Raised when data extraction fails."""


class NormalizationException(TransformationException):
    """Raised when data normalization fails."""


class FusionException(TransformationException):
    """Raised when data fusion fails."""


class ConnectorException(ApplicationException):
    """Raised when external profile fetching fails."""
