"""Transformation Service Orchestrator."""

import os
import time
from collections import defaultdict
from typing import Any, Optional

from app.models.canonical import CanonicalProfile, CanonicalField
from app.models.intermediate import RawInput, ParsedDocument, ExtractedCandidate, ExtractedValue, NormalizedCandidate, SourceType
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
            GitHubStructuredExtractor(),
            LinkedInStructuredExtractor(),
            CSVStructuredExtractor(),
        ]
        
        if os.getenv("ENABLE_NER", "false").lower() == "true":
            self.extractors.append(NERExtractor())
        
        self.priorities = {
            SourceType.RESUME_PDF: 100,
            SourceType.LINKEDIN_PROFILE: 90,
            SourceType.GITHUB_PROFILE: 80,
            SourceType.RECRUITER_CSV: 70,
        }
        
        self.fusion_engine = FusionEngine(self.priorities)

    async def transform(self, files: list[tuple[bytes, str]], github_url: Optional[str] = None, linkedin_url: Optional[str] = None, projection: dict = None) -> TransformResponse:
        start_time = time.time()
        
        raw_inputs = []
        for content, filename in files:
            ext = filename[filename.rfind("."):] if "." in filename else ""
            st = SourceType.RESUME_PDF if ext.lower() == ".pdf" else SourceType.RECRUITER_CSV
            raw_inputs.append(RawInput(source_type=st, filename=filename, content=content))
            
        if github_url:
            raw_inputs.append(RawInput(source_type=SourceType.GITHUB_PROFILE, content=b"", url=github_url))
        if linkedin_url:
            raw_inputs.append(RawInput(source_type=SourceType.LINKEDIN_PROFILE, content=b"", url=linkedin_url))

        parsed_docs: list[ParsedDocument] = []
        warnings = []
        sources_processed = []

        # 1. Connectors & Parsing
        for raw in raw_inputs:
            content_to_parse = raw.content
            filename = raw.filename or ""
            try:
                if raw.source_type == SourceType.GITHUB_PROFILE and raw.url:
                    content_to_parse = await self.github_connector.fetch_profile(raw.url)
                    filename = "github_profile.json"
                elif raw.source_type == SourceType.LINKEDIN_PROFILE and raw.url:
                    content_to_parse = await self.linkedin_connector.fetch_profile(raw.url)
                    filename = "linkedin_profile.html"
                
                ext = filename[filename.rfind("."):] if "." in filename else ""
                parser = self.parser_factory.get_parser(raw.source_type, ext)
                parsed = parser.parse(content_to_parse, raw.source_type, filename)
                parsed_docs.append(parsed)
                sources_processed.append(raw.source_type)
                warnings.extend(parsed.parse_warnings)
            except Exception as e:
                warnings.append(f"Failed parsing {raw.source_type}: {str(e)}")

        # 2. Extraction
        extracted_cands: list[ExtractedCandidate] = []
        for parsed in parsed_docs:
            all_vals = []
            cand_warnings = []
            for extractor in self.extractors:
                if parsed.source_type in extractor.supported_source_types():
                    try:
                        record = extractor.extract(parsed)
                        all_vals.extend(record.values)
                        cand_warnings.extend(record.extraction_warnings)
                    except Exception as e:
                        cand_warnings.append(str(e))
            if all_vals:
                extracted_cands.append(ExtractedCandidate(source_type=parsed.source_type, values=all_vals, extraction_warnings=cand_warnings))
            warnings.extend(cand_warnings)

        # 3. Normalization
        normalized_cands: list[NormalizedCandidate] = []
        for ext_cand in extracted_cands:
            norm_vals = []
            for val in ext_cand.values:
                norm_val = Normalizer.normalize(val)
                norm_vals.append(norm_val)
            normalized_cands.append(NormalizedCandidate(source_type=ext_cand.source_type, values=norm_vals))

        # 4. Fusion
        canonical, prov_dict, total_extracted, conflicts, overall_conf = self.fusion_engine.fuse_all(normalized_cands)

        # 5. Metadata
        metadata = CandidateMetadata(
            sources_processed=sources_processed,
            total_fields_extracted=total_extracted,
            total_conflicts_resolved=conflicts,
            overall_confidence=overall_conf,
            overall_confidence_level=ConfidenceLevel.from_score(overall_conf),
            processing_duration_ms=(time.time() - start_time) * 1000,
            warnings=warnings
        )

        # 6. Projection
        result_profile = canonical.model_dump(exclude_none=True)
        meta_dict = metadata.model_dump()
        
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
