"""Candidate repository — database access layer.

All SQL/ORM operations are isolated here. Services never touch
the database directly.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import EntityNotFoundException, RepositoryException
from app.interfaces import CandidateRepositoryInterface
from app.models.database import (
    CandidateMetadataModel, CandidateModel, SourceValueModel, TransformationRunModel,
)
from app.models.domain.candidate import (
    CandidateMetadata, CandidateRecord, CanonicalProfile, FieldProvenance,
)
from app.models.domain.enums import ConfidenceLevel, SourceType

logger = logging.getLogger(__name__)


class CandidateRepository(CandidateRepositoryInterface):
    """PostgreSQL-backed candidate repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, record: CandidateRecord) -> CandidateRecord:
        try:
            candidate_id = uuid.uuid4()
            profile = record.profile

            db_candidate = CandidateModel(
                id=candidate_id,
                full_name=profile.full_name,
                first_name=profile.first_name,
                last_name=profile.last_name,
                email=profile.email,
                phone=profile.phone,
                location=profile.location,
                current_title=profile.current_title,
                current_company=profile.current_company,
                summary=profile.summary,
                years_of_experience=profile.years_of_experience,
                skills=[s for s in profile.skills],
                experience=[e.model_dump() for e in profile.experience],
                education=[e.model_dump() for e in profile.education],
                certifications=profile.certifications,
                languages=profile.languages,
                github_url=profile.github_url,
                linkedin_url=profile.linkedin_url,
                portfolio_url=profile.portfolio_url,
                overall_confidence=record.metadata.overall_confidence,
                overall_confidence_level=record.metadata.overall_confidence_level.value,
            )
            self._session.add(db_candidate)

            # Save metadata
            db_meta = CandidateMetadataModel(
                transformation_run_id=record.metadata.transformation_run_id,
                sources_processed=[s.value for s in record.metadata.sources_processed],
                total_fields_extracted=record.metadata.total_fields_extracted,
                total_conflicts_resolved=record.metadata.total_conflicts_resolved,
                overall_confidence=record.metadata.overall_confidence,
                processing_duration_ms=record.metadata.processing_duration_ms,
                warnings=record.metadata.warnings,
            )
            db_candidate.metadata_record = db_meta

            # Save provenance as source values
            for field_name, prov in record.provenance.items():
                for cv in prov.competing_values:
                    db_sv = SourceValueModel(
                        field_name=field_name,
                        source_type=cv.get("source", "unknown"),
                        raw_value=cv.get("value"),
                        is_selected=cv.get("is_selected", False),
                        confidence=prov.confidence,
                        selection_reason=prov.reason,
                        normalizations_applied=prov.normalizations_applied,
                        extraction_method=cv.get("extraction_method"),
                    )
                    db_candidate.source_values.append(db_sv)

            # Save transformation run
            db_run = TransformationRunModel(
                status="completed",
                total_duration_ms=record.metadata.processing_duration_ms,
            )
            db_candidate.transformation_runs.append(db_run)

            await self._session.flush()

            record.id = str(candidate_id)
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

        # Load metadata
        meta_result = await self._session.execute(
            select(CandidateMetadataModel).where(CandidateMetadataModel.candidate_id == uid)
        )
        db_meta = meta_result.scalar_one_or_none()

        # Load source values for provenance
        sv_result = await self._session.execute(
            select(SourceValueModel).where(SourceValueModel.candidate_id == uid)
        )
        source_values = sv_result.scalars().all()

        return self._to_domain(candidate, db_meta, source_values)

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[CandidateRecord]:
        result = await self._session.execute(
            select(CandidateModel).order_by(CandidateModel.created_at.desc())
            .limit(limit).offset(offset)
        )
        candidates = result.scalars().all()
        records = []
        for c in candidates:
            records.append(self._to_domain(c, None, []))
        return records

    async def count(self) -> int:
        result = await self._session.execute(select(func.count(CandidateModel.id)))
        return result.scalar_one()

    def _to_domain(self, c: CandidateModel, meta: Optional[CandidateMetadataModel],
                   source_values: list) -> CandidateRecord:
        profile = CanonicalProfile(
            full_name=c.full_name, first_name=c.first_name, last_name=c.last_name,
            email=c.email, phone=c.phone, location=c.location,
            current_title=c.current_title, current_company=c.current_company,
            summary=c.summary, years_of_experience=c.years_of_experience,
            skills=c.skills or [], experience=c.experience or [],
            education=c.education or [], certifications=c.certifications or [],
            languages=c.languages or [], github_url=c.github_url,
            linkedin_url=c.linkedin_url, portfolio_url=c.portfolio_url,
        )

        metadata = CandidateMetadata(
            transformation_run_id=meta.transformation_run_id if meta else "",
            sources_processed=[SourceType(s) for s in (meta.sources_processed if meta else [])],
            total_fields_extracted=meta.total_fields_extracted if meta else 0,
            total_conflicts_resolved=meta.total_conflicts_resolved if meta else 0,
            overall_confidence=meta.overall_confidence if meta else 0.0,
            overall_confidence_level=ConfidenceLevel.from_score(meta.overall_confidence if meta else 0),
            processing_duration_ms=meta.processing_duration_ms if meta else None,
            warnings=meta.warnings if meta else [],
            created_at=c.created_at,
        )

        # Rebuild provenance from source values
        provenance: dict[str, FieldProvenance] = {}
        from collections import defaultdict
        by_field: dict[str, list] = defaultdict(list)
        for sv in source_values:
            by_field[sv.field_name].append(sv)

        for field_name, svs in by_field.items():
            selected_sv = next((s for s in svs if s.is_selected), svs[0] if svs else None)
            if selected_sv:
                try:
                    fn = FieldName(field_name)
                except ValueError:
                    continue
                provenance[field_name] = FieldProvenance(
                    field_name=fn,
                    selected_source=SourceType(selected_sv.source_type),
                    selected_value=selected_sv.raw_value,
                    competing_values=[{"source": s.source_type, "value": s.raw_value,
                                       "is_selected": s.is_selected} for s in svs],
                    reason=selected_sv.selection_reason or "",
                    confidence=selected_sv.confidence,
                    confidence_level=ConfidenceLevel.from_score(selected_sv.confidence),
                    normalizations_applied=selected_sv.normalizations_applied or [],
                    agreeing_sources=sum(1 for s in svs if s.raw_value == selected_sv.raw_value),
                    total_sources=len(svs),
                )

        return CandidateRecord(
            id=str(c.id), profile=profile, metadata=metadata, provenance=provenance,
            created_at=c.created_at, updated_at=c.updated_at,
        )
