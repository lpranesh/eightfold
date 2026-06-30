"""NER-based extraction placeholder."""

import logging
from app.interfaces.extractor import ExtractorInterface
from app.models.intermediate import ExtractedRecord, ParsedContent, SourceType
from app.core.config import settings

logger = logging.getLogger(__name__)


class NERExtractor(ExtractorInterface):
    """Optional NER extraction phase. Designed to be swapped with spaCy later."""

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.RESUME_PDF]

    def extract(self, parsed: ParsedContent) -> ExtractedRecord:
        if not settings.ENABLE_NER:
            logger.info("NER is disabled via config. Skipping.")
            return ExtractedRecord(source_type=parsed.source_type, values=[])

        # Placeholder for actual NER logic (e.g. spaCy)
        logger.info("NER extraction would run here.")
        return ExtractedRecord(source_type=parsed.source_type, values=[])
