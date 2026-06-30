"""Builds provenance records for metadata."""

from app.models.intermediate import ExtractedValue
from app.models.metadata import ConfidenceLevel, FieldProvenance


class ProvenanceBuilder:
    """Constructs provenance for each canonical field."""

    @classmethod
    def build(
        cls,
        field_name: str,
        selected: ExtractedValue,
        candidates: list[ExtractedValue],
        confidence: float
    ) -> FieldProvenance:
        
        competing = [
            {
                "value": c.raw_value,
                "source": c.source_type.value,
                "confidence": c.extraction_confidence
            }
            for c in candidates if c != selected
        ]
        
        reason = f"Selected from {selected.source_type.value} based on priority and confidence."
        
        return FieldProvenance(
            field_name=field_name,
            selected_value=selected.raw_value,
            selected_source=selected.source_type.value,
            confidence=confidence,
            confidence_level=ConfidenceLevel.from_score(confidence),
            competing_values=competing,
            reason=reason,
            normalizations_applied=["Normalizer" if selected.raw_value != selected.raw_value else "None"] # Simplified
        )
