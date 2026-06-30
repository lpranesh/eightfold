"""Deterministic fusion logic."""

from app.models.intermediate import ExtractedValue, SourceType


class FusionEngine:
    """Selects best values based on priorities."""

    def __init__(self, priorities: dict[SourceType, int]):
        self.priorities = priorities

    def fuse(self, field_name: str, candidates: list[ExtractedValue]) -> ExtractedValue:
        """Select the best candidate for a field."""
        if not candidates:
            raise ValueError("No candidates provided for fusion.")

        # Sort primarily by source priority, then by extraction confidence
        sorted_cands = sorted(
            candidates,
            key=lambda c: (self.priorities.get(c.source_type, 0), c.extraction_confidence),
            reverse=True
        )

        return sorted_cands[0]
