"""Deterministic scoring engine."""

from app.models.intermediate import ExtractedValue, SourceType


class ConfidenceEngine:
    """Calculates confidence score based on agreement and extraction quality."""

    def __init__(self, priorities: dict[SourceType, int]):
        self.priorities = priorities

    def score(self, selected: ExtractedValue, candidates: list[ExtractedValue]) -> float:
        """Compute score between 0.0 and 1.0."""
        # Base score from source priority (normalized to 0.0 - 0.5)
        source_score = self.priorities.get(selected.source_type, 50) / 200.0
        
        # Extraction quality (normalized to 0.0 - 0.3)
        ext_score = selected.extraction_confidence * 0.3
        
        # Agreement bonus (0.0 - 0.2)
        agreements = sum(1 for c in candidates if c.raw_value == selected.raw_value)
        total = len(candidates)
        agree_score = (agreements / total) * 0.2 if total > 0 else 0.0
        
        return min(1.0, source_score + ext_score + agree_score)
