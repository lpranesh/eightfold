"""Abstract interfaces for the transformation pipeline.

These ABCs define the contracts that each pipeline stage must implement.
They enable the Strategy pattern — concrete implementations can be swapped
without changing downstream modules.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.models.domain.candidate import (
    CandidateRecord,
    CanonicalProfile,
    FieldProvenance,
)
from app.models.domain.enums import FieldName, SourceType
from app.models.domain.projection import ProjectionConfig
from app.models.domain.source import ExtractedRecord, ExtractedValue, ParsedContent


class ParserInterface(ABC):
    """Contract for source document parsers.

    Each parser handles a specific file format (PDF, CSV, JSON, TXT)
    and produces a ParsedContent object.
    """

    @abstractmethod
    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        """Check if this parser can handle the given source type and extension.

        Args:
            source_type: The type of source document.
            file_extension: File extension including the dot (e.g., '.pdf').

        Returns:
            True if this parser can handle the input.
        """

    @abstractmethod
    def parse(self, content: bytes, source_type: SourceType) -> ParsedContent:
        """Parse raw file bytes into structured ParsedContent.

        Args:
            content: Raw file bytes.
            source_type: The type of source document.

        Returns:
            Parsed content ready for extraction.

        Raises:
            ParsingException: If parsing fails.
        """


class ExtractorInterface(ABC):
    """Contract for field value extractors.

    Extractors analyze parsed content and produce structured field values.
    The interface allows for rule-based, regex, or future LLM extractors.
    """

    @abstractmethod
    def supported_source_types(self) -> list[SourceType]:
        """Return the source types this extractor supports."""

    @abstractmethod
    def extract(self, parsed: ParsedContent) -> ExtractedRecord:
        """Extract structured values from parsed content.

        Args:
            parsed: The parsed content to extract from.

        Returns:
            Extracted record with field values and provenance.

        Raises:
            ExtractionException: If extraction fails.
        """


class NormalizerInterface(ABC):
    """Contract for field value normalizers.

    Normalizers clean and standardize extracted values (e.g., phone
    formats, email casing, date formats).
    """

    @abstractmethod
    def supported_fields(self) -> list[FieldName]:
        """Return the field names this normalizer handles."""

    @abstractmethod
    def normalize(self, value: ExtractedValue) -> ExtractedValue:
        """Normalize an extracted value.

        Args:
            value: The extracted value to normalize.

        Returns:
            A new ExtractedValue with the normalized value and
            normalization metadata.

        Raises:
            NormalizationException: If normalization fails.
        """


class FusionPolicyInterface(ABC):
    """Contract for field fusion policies.

    A fusion policy decides which value to select when multiple sources
    provide competing values for the same field.
    """

    @abstractmethod
    def fuse(
        self,
        field_name: FieldName,
        candidates: list[ExtractedValue],
        source_priorities: dict[str, int],
    ) -> ExtractedValue:
        """Select the best value from competing candidates.

        Args:
            field_name: The field being fused.
            candidates: All extracted values for this field.
            source_priorities: Source type to priority score mapping.

        Returns:
            The selected value.
        """


class ConfidenceEngineInterface(ABC):
    """Contract for confidence scoring."""

    @abstractmethod
    def score(
        self,
        field_name: FieldName,
        selected: ExtractedValue,
        all_candidates: list[ExtractedValue],
        source_priorities: dict[str, int],
    ) -> float:
        """Compute a deterministic confidence score for a fused field value.

        Args:
            field_name: The field being scored.
            selected: The selected/fused value.
            all_candidates: All competing values for this field.
            source_priorities: Source type to priority mapping.

        Returns:
            Confidence score between 0.0 and 1.0.
        """


class ProvenanceBuilderInterface(ABC):
    """Contract for building provenance records."""

    @abstractmethod
    def build(
        self,
        field_name: FieldName,
        selected: ExtractedValue,
        all_candidates: list[ExtractedValue],
        confidence: float,
        normalizations: list[str],
        source_priorities: dict[str, int],
    ) -> FieldProvenance:
        """Build a provenance record for a field selection.

        Args:
            field_name: The canonical field name.
            selected: The value that was chosen.
            all_candidates: All competing values considered.
            confidence: The computed confidence score.
            normalizations: List of normalizations applied.
            source_priorities: Source type to priority mapping.

        Returns:
            Complete provenance record.
        """


class ProjectionPolicyInterface(ABC):
    """Contract for projection policies.

    Projections create customized views of the canonical profile
    without modifying the underlying data.
    """

    @abstractmethod
    def project(
        self,
        profile: CanonicalProfile,
        config: ProjectionConfig,
    ) -> dict[str, Any]:
        """Apply a projection configuration to a canonical profile.

        Args:
            profile: The canonical profile to project.
            config: Projection configuration.

        Returns:
            A dictionary representing the projected view.

        Raises:
            ProjectionException: If projection fails.
        """


class CandidateRepositoryInterface(ABC):
    """Contract for candidate data persistence."""

    @abstractmethod
    async def save(self, record: CandidateRecord) -> CandidateRecord:
        """Persist a candidate record.

        Args:
            record: The candidate record to save.

        Returns:
            The saved record with generated ID.

        Raises:
            RepositoryException: If persistence fails.
        """

    @abstractmethod
    async def get_by_id(self, candidate_id: str) -> CandidateRecord:
        """Retrieve a candidate record by ID.

        Args:
            candidate_id: The candidate's unique identifier.

        Returns:
            The candidate record.

        Raises:
            EntityNotFoundException: If not found.
        """

    @abstractmethod
    async def list_all(
        self, limit: int = 50, offset: int = 0
    ) -> list[CandidateRecord]:
        """List candidate records with pagination.

        Args:
            limit: Maximum records to return.
            offset: Number of records to skip.

        Returns:
            List of candidate records.
        """
