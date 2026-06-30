"""Candidate service — business logic layer.

Orchestrates the transformation pipeline, projection, and explanation.
No SQL here — all persistence goes through the repository.
"""

import logging
from typing import Any, Optional

from app.adapters import SourceAdapter
from app.exceptions import EntityNotFoundException, ProjectionException
from app.factories import ParserFactory
from app.interfaces import CandidateRepositoryInterface
from app.models.domain.candidate import CandidateRecord
from app.models.domain.enums import FieldName, SourceType
from app.models.dto import (
    CandidateDetailResponse, CandidateListItem, CandidateListResponse,
    TransformResponse,
)
from app.services.pipeline import SourceInput, TransformationPipeline

logger = logging.getLogger(__name__)


class CandidateService:
    """Business logic for candidate operations."""

    def __init__(
        self,
        repository: CandidateRepositoryInterface,
        pipeline: TransformationPipeline,
    ) -> None:
        self._repository = repository
        self._pipeline = pipeline

    async def transform_sources(
        self,
        files: list[tuple[str, bytes, SourceType]],
    ) -> TransformResponse:
        """Run the full transformation pipeline on uploaded sources.

        Args:
            files: List of (filename, content, source_type) tuples.

        Returns:
            TransformResponse with the canonical profile.
        """
        # Build pipeline inputs
        source_inputs = [
            SourceInput(content=content, filename=filename, source_type=source_type)
            for filename, content, source_type in files
        ]

        # Run pipeline
        record = self._pipeline.transform(source_inputs)

        # Persist
        saved = await self._repository.save(record)

        return TransformResponse(
            candidate_id=saved.id or "",
            profile=saved.profile.model_dump(),
            metadata=saved.metadata.model_dump(mode="json"),
            sources_processed=[s.value for s in saved.metadata.sources_processed],
            overall_confidence=saved.metadata.overall_confidence,
            overall_confidence_level=saved.metadata.overall_confidence_level.value,
            warnings=saved.metadata.warnings,
            created_at=saved.created_at,
        )

    async def get_candidate(self, candidate_id: str) -> CandidateDetailResponse:
        """Get full candidate detail by ID."""
        record = await self._repository.get_by_id(candidate_id)
        return CandidateDetailResponse(
            id=record.id or "",
            profile=record.profile.model_dump(),
            metadata=record.metadata.model_dump(mode="json"),
            provenance={k: v.model_dump(mode="json") for k, v in record.provenance.items()},
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


    async def list_candidates(
        self, limit: int = 50, offset: int = 0,
    ) -> CandidateListResponse:
        """List all candidates with pagination."""
        records = await self._repository.list_all(limit=limit, offset=offset)
        total = await self._repository.count()
        items = [
            CandidateListItem(
                id=r.id or "",
                full_name=r.profile.full_name,
                email=r.profile.email,
                current_title=r.profile.current_title,
                sources_count=len(r.metadata.sources_processed),
                overall_confidence=r.metadata.overall_confidence,
                created_at=r.created_at,
            )
            for r in records
        ]
        return CandidateListResponse(
            candidates=items, total=total, limit=limit, offset=offset,
        )
