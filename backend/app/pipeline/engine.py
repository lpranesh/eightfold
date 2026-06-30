"""Transformation Service Orchestrator."""

import time
from collections import defaultdict
from typing import Any, Optional

from app.models.canonical import CanonicalProfile
from app.models.intermediate import ExtractedRecord, SourceType
from app.models.metadata import CandidateMetadata, ConfidenceLevel
from app.models.responses import TransformResponse

from app.sources.parser_factory import ParserFactory
from app.sources.github_connector import GitHubConnector
from app.sources.linkedin_connector import LinkedInConnector

from app.extraction.regex_extractor import RegexExtractor
from app.extraction.ner_extractor import NERExtractor
from app.extraction.structured import GitHubStructuredExtractor, LinkedInStructuredExtractor, CSVStructuredExtractor

from app.processing.normalizer import Normalizer
from app.processing.fusion import FusionEngine
from app.processing.confidence import ConfidenceEngine
from app.processing.provenance import ProvenanceBuilder
from app.processing.projection import Projector


class TransformationService:
    """Orchestrates the entire data transformation pipeline."""

    def __init__(self):
        self.parser_factory = ParserFactory()
        self.github_connector = GitHubConnector()
        self.linkedin_connector = LinkedInConnector()
        
        self.extractors = [
            RegexExtractor(),
            NERExtractor(),
            GitHubStructuredExtractor(),
            LinkedInStructuredExtractor(),
            CSVStructuredExtractor(),
        ]
        
        # Priority map for fusion
        self.priorities = {
            SourceType.RESUME_PDF: 100,
            SourceType.LINKEDIN_PROFILE: 90,
            SourceType.GITHUB_PROFILE: 80,
            SourceType.RECRUITER_CSV: 70,
        }
        
        self.fusion_engine = FusionEngine(self.priorities)
        self.confidence_engine = ConfidenceEngine(self.priorities)

    async def transform(self, files: list[tuple[bytes, str]], github_url: Optional[str] = None, linkedin_url: Optional[str] = None, projection: dict = None) -> TransformResponse:
        start_time = time.time()
        parsed_contents = []
        warnings = []
        sources_processed = []

        # 1. Connectors & Parsing
        for content, filename in files:
            ext = filename[filename.rfind("."):] if "." in filename else ""
            try:
                # Naive determination, assuming PDF/CSV
                st = SourceType.RESUME_PDF if ext == ".pdf" else SourceType.RECRUITER_CSV
                parser = self.parser_factory.get_parser(st, ext)
                parsed = parser.parse(content, st, filename)
                parsed_contents.append(parsed)
                sources_processed.append(st)
                warnings.extend(parsed.parse_warnings)
            except Exception as e:
                warnings.append(str(e))

        if github_url:
            try:
                content = await self.github_connector.fetch_profile(github_url)
                parser = self.parser_factory.get_parser(SourceType.GITHUB_PROFILE, ".json")
                parsed_contents.append(parser.parse(content, SourceType.GITHUB_PROFILE, "github.json"))
                sources_processed.append(SourceType.GITHUB_PROFILE)
            except Exception as e:
                warnings.append(str(e))
                
        if linkedin_url:
            try:
                content = await self.linkedin_connector.fetch_profile(linkedin_url)
                parser = self.parser_factory.get_parser(SourceType.LINKEDIN_PROFILE, ".json")
                parsed_contents.append(parser.parse(content, SourceType.LINKEDIN_PROFILE, "linkedin.json"))
                sources_processed.append(SourceType.LINKEDIN_PROFILE)
            except Exception as e:
                warnings.append(str(e))

        # 2. Extraction
        all_extracted: list[ExtractedRecord] = []
        for parsed in parsed_contents:
            for extractor in self.extractors:
                if parsed.source_type in extractor.supported_source_types():
                    try:
                        record = extractor.extract(parsed)
                        if record.values:
                            all_extracted.append(record)
                        warnings.extend(record.extraction_warnings)
                    except Exception as e:
                        warnings.append(str(e))

        # 3. Normalization
        for record in all_extracted:
            for i, value in enumerate(record.values):
                record.values[i] = Normalizer.normalize(value)

        # 4. Fusion & Confidence & Provenance
        field_groups = defaultdict(list)
        total_extracted = 0
        for record in all_extracted:
            for val in record.values:
                field_groups[val.field_name].append(val)
                total_extracted += 1

        profile_data = {}
        provenances = {}
        conflicts = 0
        overall_conf_sum = 0.0

        for field, candidates in field_groups.items():
            if len(candidates) > 1:
                conflicts += 1
                
            selected = self.fusion_engine.fuse(field, candidates)
            conf = self.confidence_engine.score(selected, candidates)
            overall_conf_sum += conf
            
            prov = ProvenanceBuilder.build(field, selected, candidates, conf)
            
            profile_data[field] = selected.raw_value
            provenances[field] = prov.model_dump()

        canonical = CanonicalProfile(**profile_data)
        
        overall_confidence = overall_conf_sum / len(field_groups) if field_groups else 0.0

        metadata = CandidateMetadata(
            sources_processed=sources_processed,
            total_fields_extracted=total_extracted,
            total_conflicts_resolved=conflicts,
            overall_confidence=overall_confidence,
            overall_confidence_level=ConfidenceLevel.from_score(overall_confidence),
            processing_duration_ms=(time.time() - start_time) * 1000,
            warnings=warnings
        )

        # 5. Projection
        result_profile = canonical.model_dump(exclude_none=True)
        meta_dict = metadata.model_dump()
        prov_dict = provenances
        
        if projection:
            result_profile = Projector.project(canonical, projection)
            if projection.hide_metadata:
                meta_dict = None
            if not projection.include_provenance:
                prov_dict = None

        return TransformResponse(
            profile=result_profile,
            metadata=meta_dict,
            provenance=prov_dict,
            warnings=warnings
        )
