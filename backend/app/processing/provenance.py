"""Generates explanation metadata."""

from app.models.intermediate import ExtractedValue
from app.models.metadata import FieldProvenance, ConfidenceLevel


class ProvenanceBuilder:
    """Builds explainable provenance records."""

    @classmethod
    def build(cls, field: str, selected: ExtractedValue, candidates: list[ExtractedValue], confidence: float) -> FieldProvenance:
        """Constructs provenance for a selected field."""
        
        competing = []
        for c in candidates:
            # Add all other candidates as competing values, including identical ones from different sources
            if c != selected:
                competing.append({
                    "source": c.source_type,
                    "value": c.raw_value,
                    "confidence": c.extraction_confidence
                })

        reason = f"Selected from {selected.source_type} due to source priority and {len(candidates)} matching data points."

        return FieldProvenance(
            field_name=field,
            selected_source=selected.source_type,
            selected_value=selected.raw_value,
            competing_values=competing,
            reason=reason,
            confidence=confidence,
            confidence_level=ConfidenceLevel.from_score(confidence),
            normalizations_applied=selected.normalizations
        )
