"""Deterministic fusion logic."""

from collections import defaultdict
from app.models.intermediate import NormalizedCandidate, ExtractedValue, SourceType
from app.models.canonical import CanonicalProfile, CanonicalField
from app.processing.confidence import ConfidenceEngine
from app.processing.provenance import ProvenanceBuilder

class FusionEngine:
    """Selects best values based on priorities and groups them."""

    def __init__(self, priorities: dict[SourceType, int]):
        self.priorities = priorities
        self.confidence_engine = ConfidenceEngine(priorities)

    def fuse_all(self, normalized_cands: list[NormalizedCandidate]) -> tuple[CanonicalProfile, dict, int, int, float]:
        field_groups = defaultdict(list)
        total_extracted = 0

        for cand in normalized_cands:
            for val in cand.values:
                field_groups[val.field_name].append(val)
                total_extracted += 1

        profile_data = {}
        provenances = {}
        conflicts = 0
        overall_conf_sum = 0.0
        
        array_fields = {"education", "experience", "skills", "certifications", "languages", "emails", "phones"}

        for field, candidates in field_groups.items():
            if len(candidates) > 1:
                conflicts += 1
                
            if field in array_fields:
                # Group by identical raw values
                unique_groups = self._group_identical(candidates)
                fused_list = []
                for group in unique_groups:
                    selected, conf = self._fuse_group(group, group) # The group is the candidates here
                    fused_list.append(
                        CanonicalField(
                            value=selected.raw_value,
                            confidence=conf,
                            sources=[c.source_type for c in group]
                        )
                    )
                profile_data[field] = fused_list
                # For arrays, provenance might be complex, we just store the first group's provenance for simplicity in this assignment
                if unique_groups:
                    best_group = unique_groups[0]
                    selected, conf = self._fuse_group(best_group, best_group)
                    overall_conf_sum += conf
                    prov = ProvenanceBuilder.build(field, selected, best_group, conf)
                    provenances[field] = prov.model_dump()
            else:
                # Group by identical to find the best, but only pick ONE winner
                unique_groups = self._group_identical(candidates)
                # Sort groups by highest priority element
                unique_groups.sort(key=lambda g: max([self.priorities.get(c.source_type, 0) for c in g]), reverse=True)
                
                best_group = unique_groups[0]
                selected, conf = self._fuse_group(best_group, candidates) # Compare against ALL candidates for agreement penalty
                
                overall_conf_sum += conf
                
                profile_data[field] = CanonicalField(
                    value=selected.raw_value,
                    confidence=conf,
                    sources=[c.source_type for c in best_group]
                )
                
                prov = ProvenanceBuilder.build(field, selected, candidates, conf)
                provenances[field] = prov.model_dump()

        canonical = CanonicalProfile(**profile_data)
        overall_conf = overall_conf_sum / len(field_groups) if field_groups else 0.0
        
        return canonical, provenances, total_extracted, conflicts, overall_conf
        
    def _group_identical(self, candidates: list[ExtractedValue]) -> list[list[ExtractedValue]]:
        groups = defaultdict(list)
        for c in candidates:
            # We group by the normalized value (which is raw_value since Normalizer updated it)
            # stringify just in case it's dict
            groups[str(c.raw_value)].append(c)
        return list(groups.values())

    def _fuse_group(self, identical_group: list[ExtractedValue], all_candidates: list[ExtractedValue]) -> tuple[ExtractedValue, float]:
        """Select the highest priority representation from the identical group and compute score."""
        sorted_cands = sorted(
            identical_group,
            key=lambda c: (self.priorities.get(c.source_type, 0), c.extraction_confidence),
            reverse=True
        )
        selected = sorted_cands[0]
        conf = self.confidence_engine.score(selected, all_candidates, identical_group)
        return selected, conf
