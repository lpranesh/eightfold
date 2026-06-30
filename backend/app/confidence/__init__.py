"""Deterministic confidence scoring engine.

Computes confidence scores based on:
- Number of agreeing sources
- Source priority of the selected source
- Extraction confidence of the selected value
- Field completeness (non-empty value)
"""

import logging

from app.interfaces import ConfidenceEngineInterface
from app.models.domain.enums import FieldName
from app.models.domain.source import ExtractedValue

logger = logging.getLogger(__name__)

# Weights for each factor in the confidence formula
_W_AGREEMENT = 0.35
_W_PRIORITY = 0.25
_W_EXTRACTION = 0.25
_W_COMPLETENESS = 0.15


class DeterministicConfidenceEngine(ConfidenceEngineInterface):
    """Compute confidence deterministically from measurable factors.

    Formula:
        score = (agreement_ratio * W_AGREEMENT +
                 priority_ratio * W_PRIORITY +
                 extraction_confidence * W_EXTRACTION +
                 completeness * W_COMPLETENESS)
    """

    def score(
        self,
        field_name: FieldName,
        selected: ExtractedValue,
        all_candidates: list[ExtractedValue],
        source_priorities: dict[str, int],
    ) -> float:
        total = len(all_candidates)
        if total == 0:
            return 0.0

        # Agreement: how many sources agree with selected value
        selected_key = self._value_key(selected.raw_value)
        agreeing = sum(
            1 for c in all_candidates
            if self._value_key(c.raw_value) == selected_key
        )
        agreement_ratio = agreeing / total

        # Priority: how high-priority is the selected source (0-1)
        max_priority = max(source_priorities.values()) if source_priorities else 1
        selected_priority = source_priorities.get(selected.source_type.value, 0)
        priority_ratio = selected_priority / max_priority if max_priority > 0 else 0

        # Extraction confidence from the extractor itself
        extraction = selected.extraction_confidence

        # Completeness: is the value non-trivial?
        completeness = 1.0 if self._is_complete(selected.raw_value) else 0.3

        score = (
            agreement_ratio * _W_AGREEMENT
            + priority_ratio * _W_PRIORITY
            + extraction * _W_EXTRACTION
            + completeness * _W_COMPLETENESS
        )

        # Clamp to [0, 1]
        return max(0.0, min(1.0, round(score, 4)))

    def _value_key(self, value: object) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        if isinstance(value, list):
            return str(sorted(str(v).lower() for v in value))
        return str(value).lower()

    def _is_complete(self, value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return len(value.strip()) > 0
        if isinstance(value, list):
            return len(value) > 0
        return True
