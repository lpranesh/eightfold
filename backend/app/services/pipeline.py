"""Transformation pipeline orchestrator.

Composes all pipeline stages into a single, linear transformation flow:
Parse → Extract → Normalize → Fuse → Score → Provenance → Build → Validate
"""

import logging
import time
import uuid
from collections import defaultdict
from typing import Any, Optional

from app.confidence import DeterministicConfidenceEngine
from app.exceptions import FusionException, ValidationException
from app.extractors.resume_extractor import ResumeExtractor
from app.extractors.structured_extractors import (
    CSVExtractor, RecruiterNotesExtractor,
)
from app.factories import ParserFactory
from app.fusion import get_fusion_policy
from app.interfaces import ConfidenceEngineInterface, ExtractorInterface, NormalizerInterface
from app.models.domain.candidate import (
    CandidateMetadata, CandidateRecord, CanonicalProfile, FieldProvenance,
)
from app.models.domain.enums import ConfidenceLevel, FieldName, SourceType, TransformationStatus
from app.models.domain.source import ExtractedCandidate, ExtractedValue, ParsedDocument
from app.normalizers import get_all_normalizers
from app.provenance import DefaultProvenanceBuilder

logger = logging.getLogger(__name__)


class SourceInput:
    """A single source file to be processed by the pipeline."""

    def __init__(self, content: bytes, filename: str, source_type: SourceType) -> None:
        self.content = content
        self.filename = filename
        self.source_type = source_type
        self.file_extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


class PipelineResult:
    """Result of a pipeline stage, carrying data and stage metadata."""

    def __init__(self) -> None:
        self.stages: list[dict[str, Any]] = []
        self.warnings: list[str] = []

    def add_stage(self, name: str, status: str, duration_ms: float,
                  items: int = 0, warnings: Optional[list[str]] = None) -> None:
        self.stages.append({
            "name": name, "status": status, "duration_ms": round(duration_ms, 2),
            "items_processed": items, "warnings": warnings or [],
        })
        if warnings:
            self.warnings.extend(warnings)


class TransformationPipeline:
    """Orchestrates the full candidate data transformation pipeline.

    All dependencies are injected. The pipeline is stateless — each
    invocation creates a fresh transformation run.
    """

    def __init__(
        self,
        parser_factory: ParserFactory,
        extractors: Optional[list[ExtractorInterface]] = None,
        normalizers: Optional[list[NormalizerInterface]] = None,
        confidence_engine: Optional[ConfidenceEngineInterface] = None,
        source_priorities: Optional[dict[str, int]] = None,
    ) -> None:
        self._parser_factory = parser_factory
        self._extractors = extractors or self._default_extractors()
        self._normalizers = normalizers or get_all_normalizers()
        self._confidence_engine = confidence_engine or DeterministicConfidenceEngine()
        self._provenance_builder = DefaultProvenanceBuilder()
        self._source_priorities = source_priorities or {
            "resume": 90, "linkedin": 85, "ats_json": 80,
            "github": 70, "recruiter_csv": 60, "recruiter_notes": 50,
        }
        # Build normalizer lookup
        self._normalizer_map: dict[FieldName, NormalizerInterface] = {}
        for n in self._normalizers:
            for field in n.supported_fields():
                self._normalizer_map[field] = n
        # Build extractor lookup
        self._extractor_map: dict[SourceType, ExtractorInterface] = {}
        for e in self._extractors:
            for st in e.supported_source_types():
                self._extractor_map[st] = e

    def transform(self, sources: list[SourceInput]) -> CandidateRecord:
        """Execute the full transformation pipeline.

        Args:
            sources: List of source files to process.

        Returns:
            A complete CandidateRecord with profile, metadata, and provenance.
        """
        start_time = time.monotonic()
        run_id = str(uuid.uuid4())
        result = PipelineResult()

        # Stage 1: Parse
        parsed_contents = self._stage_parse(sources, result)

        # Stage 2: Extract
        extracted_records = self._stage_extract(parsed_contents, result)

        # Stage 3: Normalize
        normalized_records = self._stage_normalize(extracted_records, result)

        # Stage 4: Fuse + Confidence + Provenance
        profile, provenance, conflicts = self._stage_fuse(normalized_records, result)

        # Stage 5: Validate
        self._stage_validate(profile, result)

        duration_ms = (time.monotonic() - start_time) * 1000

        # Compute overall confidence
        if provenance:
            scores = [p.confidence for p in provenance.values()]
            overall = sum(scores) / len(scores)
        else:
            overall = 0.0

        metadata = CandidateMetadata(
            transformation_run_id=run_id,
            sources_processed=[s.source_type for s in sources],
            total_fields_extracted=sum(len(r.values) for r in extracted_records),
            total_conflicts_resolved=conflicts,
            overall_confidence=round(overall, 4),
            overall_confidence_level=ConfidenceLevel.from_score(overall),
            processing_duration_ms=round(duration_ms, 2),
            warnings=result.warnings,
        )

        return CandidateRecord(
            profile=profile,
            metadata=metadata,
            provenance=provenance,
        )

    def _stage_parse(self, sources: list[SourceInput], result: PipelineResult) -> list[ParsedDocument]:
        start = time.monotonic()
        parsed: list[ParsedDocument] = []
        warnings: list[str] = []

        for source in sources:
            try:
                parser = self._parser_factory.get_parser(source.source_type, source.file_extension)
                content = parser.parse(source.content, source.source_type)
                parsed.append(content)
                warnings.extend(content.parse_warnings)
            except Exception as exc:
                msg = f"Failed to parse {source.filename}: {exc}"
                logger.warning(msg)
                warnings.append(msg)

        result.add_stage("parse", "completed", (time.monotonic() - start) * 1000,
                         items=len(parsed), warnings=warnings)
        return parsed

    def _stage_extract(self, parsed: list[ParsedDocument], result: PipelineResult) -> list[ExtractedCandidate]:
        start = time.monotonic()
        records: list[ExtractedCandidate] = []
        warnings: list[str] = []

        for content in parsed:
            extractor = self._extractor_map.get(content.source_type)
            if not extractor:
                warnings.append(f"No extractor for {content.source_type.value}")
                continue
            try:
                record = extractor.extract(content)
                records.append(record)
                warnings.extend(record.extraction_warnings)
            except Exception as exc:
                msg = f"Extraction failed for {content.source_type.value}: {exc}"
                logger.warning(msg)
                warnings.append(msg)

        result.add_stage("extract", "completed", (time.monotonic() - start) * 1000,
                         items=sum(len(r.values) for r in records), warnings=warnings)
        return records

    def _stage_normalize(self, records: list[ExtractedCandidate], result: PipelineResult) -> list[ExtractedCandidate]:
        start = time.monotonic()
        normalized: list[ExtractedCandidate] = []
        norm_count = 0

        for record in records:
            new_values: list[ExtractedValue] = []
            for value in record.values:
                normalizer = self._normalizer_map.get(value.field_name)
                if normalizer:
                    try:
                        value = normalizer.normalize(value)
                        norm_count += 1
                    except Exception as exc:
                        logger.warning("Normalization failed for %s: %s", value.field_name.value, exc)
                new_values.append(value)
            normalized.append(ExtractedCandidate(
                source_type=record.source_type,
                values=new_values,
                extraction_warnings=record.extraction_warnings,
                extracted_at=record.extracted_at,
            ))

        result.add_stage("normalize", "completed", (time.monotonic() - start) * 1000, items=norm_count)
        return normalized

    def _stage_fuse(self, records: list[ExtractedCandidate], result: PipelineResult
                    ) -> tuple[CanonicalProfile, dict[str, FieldProvenance], int]:
        start = time.monotonic()

        # Group all values by field name
        field_values: dict[FieldName, list[ExtractedValue]] = defaultdict(list)
        for record in records:
            for value in record.values:
                field_values[value.field_name].append(value)

        profile_data: dict[str, Any] = {}
        provenance: dict[str, FieldProvenance] = {}
        conflicts = 0

        for field_name, candidates in field_values.items():
            if len(candidates) > 1:
                conflicts += 1
            policy = get_fusion_policy(field_name)
            selected = policy.fuse(field_name, candidates, self._source_priorities)

            # Score confidence
            confidence = self._confidence_engine.score(
                field_name, selected, candidates, self._source_priorities
            )

            # Build provenance
            normalizer = self._normalizer_map.get(field_name)
            normalizations = [type(normalizer).__name__] if normalizer else []
            prov = self._provenance_builder.build(
                field_name, selected, candidates, confidence,
                normalizations, self._source_priorities,
            )
            provenance[field_name.value] = prov
            profile_data[field_name.value] = selected.raw_value

        try:
            profile = CanonicalProfile(**profile_data)
        except Exception as exc:
            raise FusionException(message=f"Failed to build canonical profile: {exc}")

        result.add_stage("fuse", "completed", (time.monotonic() - start) * 1000,
                         items=len(profile_data))
        return profile, provenance, conflicts

    def _stage_validate(self, profile: CanonicalProfile, result: PipelineResult) -> None:
        start = time.monotonic()
        warnings: list[str] = []

        # Validate that we have at least some useful data
        data = profile.model_dump(exclude_none=True)
        if len(data) == 0:
            raise ValidationException(message="Canonical profile is completely empty")

        if not profile.full_name and not profile.email:
            warnings.append("Profile missing both name and email — identity may be ambiguous")

        result.add_stage("validate", "completed", (time.monotonic() - start) * 1000, warnings=warnings)

    @staticmethod
    def _default_extractors() -> list[ExtractorInterface]:
        return [
            ResumeExtractor(),
            CSVExtractor(),
            RecruiterNotesExtractor(),
        ]
