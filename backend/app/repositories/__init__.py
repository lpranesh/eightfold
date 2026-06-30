"""Candidate repository — database access layer.

All SQL/ORM operations are isolated here. Services never touch
the database directly.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import EntityNotFoundException, RepositoryException
from app.interfaces import CandidateRepositoryInterface
from app.models.database import CandidateModel
from app.models.domain.candidate import CandidateRecord

logger = logging.getLogger(__name__)


class CandidateRepository(CandidateRepositoryInterface):
    """PostgreSQL-backed candidate repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, record: CandidateRecord) -> CandidateRecord:
        try:
            if not record.id:
                record.id = str(uuid.uuid4())
                
            db_candidate = CandidateModel(
                id=uuid.UUID(record.id),
                canonical_profile=record.profile.model_dump(mode="json"),
                metadata_record=record.metadata.model_dump(mode="json"),
                provenance_record={k: v.model_dump(mode="json") for k, v in record.provenance.items()},
            )
            self._session.add(db_candidate)
            await self._session.flush()

            return record

        except Exception as exc:
            logger.error("Failed to save candidate", exc_info=exc)
            raise RepositoryException(message=f"Failed to save candidate: {exc}")

    async def get_by_id(self, candidate_id: str) -> CandidateRecord:
        try:
            uid = uuid.UUID(candidate_id)
        except ValueError:
            raise EntityNotFoundException(message=f"Invalid candidate ID format: {candidate_id}")

        result = await self._session.execute(
            select(CandidateModel).where(CandidateModel.id == uid)
        )
        candidate = result.scalar_one_or_none()
        if not candidate:
            raise EntityNotFoundException(message=f"Candidate {candidate_id} not found")

        return self._to_domain(candidate)

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[CandidateRecord]:
        result = await self._session.execute(
            select(CandidateModel).order_by(CandidateModel.created_at.desc())
            .limit(limit).offset(offset)
        )
        candidates = result.scalars().all()
        return [self._to_domain(c) for c in candidates]

    async def count(self) -> int:
        result = await self._session.execute(select(func.count(CandidateModel.id)))
        return result.scalar_one()

    def _to_domain(self, c: CandidateModel) -> CandidateRecord:
        # Reconstruct the CandidateRecord purely from the JSONB data
        from app.models.domain.candidate import CanonicalProfile, CandidateMetadata, FieldProvenance

        profile = CanonicalProfile.model_validate(c.canonical_profile)
        metadata = CandidateMetadata.model_validate(c.metadata_record)
        provenance = {k: FieldProvenance.model_validate(v) for k, v in c.provenance_record.items()}
        
        return CandidateRecord(
            id=str(c.id),
            profile=profile,
            metadata=metadata,
            provenance=provenance,
            created_at=c.created_at,
            updated_at=c.created_at,
        )
