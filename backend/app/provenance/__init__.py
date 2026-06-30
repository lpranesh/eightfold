"""Provenance builder — records why each field value was selected."""

import logging

from app.interfaces import ProvenanceBuilderInterface
from app.models.domain.candidate import FieldProvenance
from app.models.domain.enums import ConfidenceLevel, FieldName
from app.models.domain.source import ExtractedValue

logger = logging.getLogger(__name__)


class DefaultProvenanceBuilder(ProvenanceBuilderInterface):
    """Build provenance records with human-readable explanations."""

    def build(
        self,
        field_name: FieldName,
        selected: ExtractedValue,
        all_candidates: list[ExtractedValue],
        confidence: float,
        normalizations: list[str],
        source_priorities: dict[str, int],
    ) -> FieldProvenance:
        total = len(all_candidates)
        selected_key = self._value_key(selected.raw_value)
        agreeing = sum(1 for c in all_candidates if self._value_key(c.raw_value) == selected_key)

        # Build competing values list
        competing = []
        for c in all_candidates:
            competing.append({
                "source": c.source_type.value,
                "value": c.raw_value,
                "extraction_method": c.extraction_method,
                "extraction_confidence": c.extraction_confidence,
                "is_selected": c.source_type == selected.source_type,
            })

        reason = self._build_reason(field_name, selected, all_candidates,
                                     agreeing, total, source_priorities)

        return FieldProvenance(
            field_name=field_name,
            selected_source=selected.source_type,
            selected_value=selected.raw_value,
            competing_values=competing,
            reason=reason,
            confidence=confidence,
            confidence_level=ConfidenceLevel.from_score(confidence),
            normalizations_applied=normalizations,
            agreeing_sources=agreeing,
            total_sources=total,
        )

    def _build_reason(self, field_name: FieldName, selected: ExtractedValue,
                       all_candidates: list[ExtractedValue], agreeing: int,
                       total: int, source_priorities: dict[str, int]) -> str:
        parts: list[str] = []

        if total == 1:
            parts.append(f"Only source for {field_name.value}")
        elif agreeing == total:
            parts.append(f"All {total} sources agree")
        elif agreeing > total / 2:
            parts.append(f"Majority agreement ({agreeing}/{total} sources)")
        else:
            priority = source_priorities.get(selected.source_type.value, 0)
            parts.append(f"Selected from {selected.source_type.value} (priority={priority})")

        parts.append(f"Extracted via {selected.extraction_method}")
        parts.append(f"Extraction confidence: {selected.extraction_confidence:.0%}")

        return ". ".join(parts) + "."

    def _value_key(self, value: object) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        if isinstance(value, list):
            return str(sorted(str(v).lower() for v in value))
        return str(value).lower()
