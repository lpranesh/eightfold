"""Adapters convert heterogeneous inputs into pipeline-ready models."""

import logging
import os
from typing import Optional

from app.models.domain.enums import SourceType

logger = logging.getLogger(__name__)

# Map file extension + source type to the correct SourceType
_EXTENSION_MAP: dict[str, list[SourceType]] = {
    ".pdf": [SourceType.RESUME],
    ".csv": [SourceType.RECRUITER_CSV],
    ".txt": [SourceType.RECRUITER_NOTES],
}


class SourceAdapter:
    """Converts raw upload metadata into validated SourceType mappings.

    This adapter sits between the API layer and the pipeline,
    ensuring inputs are properly identified before processing.
    """

    @staticmethod
    def resolve_source_type(
        filename: str,
        declared_type: Optional[SourceType] = None,
    ) -> SourceType:
        """Determine the source type from filename and optional declaration.

        Args:
            filename: The uploaded filename.
            declared_type: An explicitly declared source type from the user.

        Returns:
            The resolved SourceType.
        """
        if declared_type is not None:
            return declared_type

        ext = os.path.splitext(filename)[1].lower()
        candidates = _EXTENSION_MAP.get(ext, [])
        if len(candidates) == 1:
            return candidates[0]

        lower_name = filename.lower()
        if "resume" in lower_name or "cv" in lower_name:
            return SourceType.RESUME
        if "note" in lower_name or "recruiter" in lower_name:
            return SourceType.RECRUITER_NOTES

        logger.warning("Could not resolve source type for %s, defaulting to RECRUITER_NOTES", filename)
        return SourceType.RECRUITER_NOTES

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Extract the file extension from a filename."""
        return os.path.splitext(filename)[1].lower()
