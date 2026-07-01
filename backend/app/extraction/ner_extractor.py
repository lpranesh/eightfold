"""NER Extractor using GLiNER."""

from app.interfaces.extractor import ExtractorInterface
from app.models.intermediate import ParsedDocument, ExtractedCandidate, ExtractedValue, SourceType
from app.core.config import settings

class NERExtractor(ExtractorInterface):
    """Uses GLiNER to perform zero-shot Named Entity Recognition."""
    
    def __init__(self):
        self.enabled = False
        self.model = None

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.RESUME_PDF]

    def extract(self, parsed: ParsedDocument) -> ExtractedCandidate:
        record = ExtractedCandidate(source_type=parsed.source_type, values=[])
        if not self.enabled or not parsed.raw_text or not self.model:
            return record
            
        labels = ["job title", "company", "skill", "university", "degree"]
        
        # In a real scenario, chunking the text might be necessary.
        text = parsed.raw_text[:2000] # limiting length for memory
        try:
            entities = self.model.predict_entities(text, labels)
            
            for ent in entities:
                label = ent["label"].lower()
                text_val = ent["text"]
                score = float(ent["score"])
                
                field_map = {
                    "job title": "current_title",
                    "company": "current_company",
                    "skill": "skills",
                    "university": "education",
                    "degree": "education"
                }
                
                if label in field_map:
                    # For skills/education which are arrays, we return them individually
                    # The fusion engine will combine them later
                    record.values.append(
                        ExtractedValue(
                            field_name=field_map[label],
                            raw_value=text_val,
                            source_type=parsed.source_type,
                            extraction_method="GLiNER",
                            extraction_confidence=score
                        )
                    )
        except Exception as e:
            record.extraction_warnings.append(f"GLiNER inference failed: {e}")
            
        return record
