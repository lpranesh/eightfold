"""Deterministic scoring engine."""

from app.models.intermediate import ExtractedValue, SourceType


class ConfidenceEngine:
    """Calculates confidence score based on agreement and extraction quality."""

    def __init__(self, priorities: dict[SourceType, int]):
        self.priorities = priorities

    def score(self, selected: ExtractedValue, all_candidates: list[ExtractedValue], identical_group: list[ExtractedValue]) -> float:
        """Compute score between 0.0 and 1.0 deterministically."""
        # Base score from source priority (normalized to 0.0 - 0.5)
        source_score = self.priorities.get(selected.source_type, 50) / 200.0
        
        # Extraction quality (normalized to 0.0 - 0.2)
        ext_score = selected.extraction_confidence * 0.2
        
        # Agreement bonus (0.0 - 0.2)
        agreements = len(identical_group)
        total = len(all_candidates)
        agree_score = (agreements / total) * 0.2 if total > 0 else 0.0
        
        # Normalization success (if we had normalizations applied)
        # We give a small flat bonus 0.1 for successful deterministic formatting
        norm_score = 0.1 if selected.normalizations else 0.0
        
        return min(1.0, source_score + ext_score + agree_score + norm_score)
