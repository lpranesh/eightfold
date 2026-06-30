"""Fusion engine — resolves conflicts when multiple sources provide the same field.

Uses source priority, agreement count, and extraction confidence
to select the best value deterministically.
"""

import logging
from typing import Any

from app.interfaces import FusionPolicyInterface
from app.models.domain.enums import FieldName, SourceType
from app.models.domain.source import ExtractedValue

logger = logging.getLogger(__name__)


class PriorityBasedFusionPolicy(FusionPolicyInterface):
    """Fuse competing values using source priority and agreement.

    Selection algorithm:
    1. If all sources agree on the value, select from highest-priority source.
    2. If majority agrees, select the majority value from highest-priority source.
    3. Otherwise, select from the highest-priority source.
    """

    def fuse(
        self,
        field_name: FieldName,
        candidates: list[ExtractedValue],
        source_priorities: dict[str, int],
    ) -> ExtractedValue:
        if len(candidates) == 1:
            return candidates[0]

        # Group by normalized value
        value_groups: dict[str, list[ExtractedValue]] = {}
        for c in candidates:
            key = self._normalize_for_comparison(c.raw_value)
            value_groups.setdefault(key, []).append(c)

        # Find majority group
        majority_group = max(value_groups.values(), key=len)
        majority_count = len(majority_group)

        if majority_count > len(candidates) / 2:
            # Majority agrees — pick from highest priority within majority
            selected = max(
                majority_group,
                key=lambda v: source_priorities.get(v.source_type.value, 0),
            )
            logger.debug("Fused %s: majority agreement (%d/%d)", field_name.value,
                         majority_count, len(candidates))
        else:
            # No majority — pick from highest priority source
            selected = max(
                candidates,
                key=lambda v: (
                    source_priorities.get(v.source_type.value, 0),
                    v.extraction_confidence,
                ),
            )
            logger.debug("Fused %s: highest priority source (%s)", field_name.value,
                         selected.source_type.value)

        return selected

    def _normalize_for_comparison(self, value: Any) -> str:
        """Create a comparison key from a value."""
        if isinstance(value, str):
            return value.strip().lower()
        if isinstance(value, list):
            return str(sorted(str(v).lower() for v in value))
        return str(value).lower()


class ListMergeFusionPolicy(FusionPolicyInterface):
    """Fuse list-type fields by merging and deduplicating."""

    def fuse(
        self,
        field_name: FieldName,
        candidates: list[ExtractedValue],
        source_priorities: dict[str, int],
    ) -> ExtractedValue:
        merged: list[Any] = []
        seen: set[str] = set()
        # Sort by source priority (highest first)
        sorted_candidates = sorted(
            candidates,
            key=lambda v: source_priorities.get(v.source_type.value, 0),
            reverse=True,
        )
        for c in sorted_candidates:
            items = c.raw_value if isinstance(c.raw_value, list) else [c.raw_value]
            for item in items:
                key = str(item).strip().lower()
                if key not in seen:
                    seen.add(key)
                    merged.append(item)

        # Use highest-priority source for provenance
        best = sorted_candidates[0]
        return ExtractedValue(
            field_name=field_name, raw_value=merged,
            source_type=best.source_type, extraction_method="list_merge",
            extraction_confidence=best.extraction_confidence,
        )


# Fields that should use list merge instead of priority-based selection
LIST_FIELDS = {FieldName.SKILLS, FieldName.CERTIFICATIONS, FieldName.LANGUAGES}


def get_fusion_policy(field_name: FieldName) -> FusionPolicyInterface:
    """Return the appropriate fusion policy for a field."""
    if field_name in LIST_FIELDS:
        return ListMergeFusionPolicy()
    return PriorityBasedFusionPolicy()
