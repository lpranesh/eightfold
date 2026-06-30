"""Tests for parsers, extractors, normalizers, fusion, confidence, and pipeline."""

import json
import pytest

from app.models.domain.enums import FieldName, SourceType, ConfidenceLevel
from app.models.domain.source import ParsedContent, ExtractedValue, ExtractedRecord
from app.models.domain.projection import ProjectionConfig
from app.models.domain.candidate import CanonicalProfile


# ---- Parser Tests ----

class TestCSVParser:
    def test_parse_valid_csv(self):
        from app.parsers.csv_parser import CSVParser
        parser = CSVParser()
        csv_data = b"name,email,phone\nJohn Doe,john@example.com,555-1234"
        result = parser.parse(csv_data, SourceType.RECRUITER_CSV)
        assert result.source_type == SourceType.RECRUITER_CSV
        assert result.structured_data is not None
        assert result.structured_data["row_count"] == 1
        row = result.structured_data["rows"][0]
        assert row["name"] == "John Doe"
        assert row["email"] == "john@example.com"

    def test_can_parse_csv(self):
        from app.parsers.csv_parser import CSVParser
        parser = CSVParser()
        assert parser.can_parse(SourceType.RECRUITER_CSV, ".csv")
        assert not parser.can_parse(SourceType.RECRUITER_CSV, ".json")


class TestJSONParser:
    def test_parse_valid_json(self):
        from app.parsers.json_parser import JSONParser
        parser = JSONParser()
        data = {"name": "Jane", "email": "jane@test.com"}
        result = parser.parse(json.dumps(data).encode(), SourceType.ATS_JSON)
        assert result.structured_data == data

    def test_parse_json_array(self):
        from app.parsers.json_parser import JSONParser
        parser = JSONParser()
        data = [{"id": 1}, {"id": 2}]
        result = parser.parse(json.dumps(data).encode(), SourceType.ATS_JSON)
        assert "items" in result.structured_data

    def test_parse_invalid_json(self):
        from app.parsers.json_parser import JSONParser
        from app.exceptions import ParsingException
        parser = JSONParser()
        with pytest.raises(ParsingException):
            parser.parse(b"not json", SourceType.ATS_JSON)


class TestTextParser:
    def test_parse_text(self):
        from app.parsers.text_parser import TextParser
        parser = TextParser()
        result = parser.parse(b"Some recruiter notes", SourceType.RECRUITER_NOTES)
        assert result.raw_text == "Some recruiter notes"


# ---- Extractor Tests ----

class TestResumeExtractor:
    def test_extract_email(self):
        from app.extractors.resume_extractor import ResumeExtractor
        ext = ResumeExtractor()
        parsed = ParsedContent(
            source_type=SourceType.RESUME,
            raw_text="John Doe\njohn@example.com\n555-123-4567",
        )
        result = ext.extract(parsed)
        emails = [v for v in result.values if v.field_name == FieldName.EMAIL]
        assert len(emails) == 1
        assert emails[0].raw_value == "john@example.com"

    def test_extract_name(self):
        from app.extractors.resume_extractor import ResumeExtractor
        ext = ResumeExtractor()
        parsed = ParsedContent(
            source_type=SourceType.RESUME,
            raw_text="John Doe\njohn@example.com\n\nExperience\n...",
        )
        result = ext.extract(parsed)
        names = [v for v in result.values if v.field_name == FieldName.FULL_NAME]
        assert len(names) == 1
        assert names[0].raw_value == "John Doe"


class TestStructuredExtractors:
    def test_ats_extractor(self):
        from app.extractors.structured_extractors import ATSExtractor
        ext = ATSExtractor()
        parsed = ParsedContent(
            source_type=SourceType.ATS_JSON,
            structured_data={"name": "Alice", "email": "alice@test.com", "skills": ["Python"]},
        )
        result = ext.extract(parsed)
        assert any(v.field_name == FieldName.FULL_NAME and v.raw_value == "Alice" for v in result.values)
        assert any(v.field_name == FieldName.EMAIL for v in result.values)

    def test_github_extractor(self):
        from app.extractors.structured_extractors import GitHubExtractor
        ext = GitHubExtractor()
        parsed = ParsedContent(
            source_type=SourceType.GITHUB,
            structured_data={"name": "Bob", "login": "bobdev", "bio": "Developer"},
        )
        result = ext.extract(parsed)
        github_urls = [v for v in result.values if v.field_name == FieldName.GITHUB_URL]
        assert len(github_urls) == 1
        assert "bobdev" in github_urls[0].raw_value


# ---- Normalizer Tests ----

class TestNormalizers:
    def test_email_normalizer(self):
        from app.normalizers import EmailNormalizer
        n = EmailNormalizer()
        v = ExtractedValue(field_name=FieldName.EMAIL, raw_value="  John@Test.COM  ",
                           source_type=SourceType.RESUME, extraction_method="regex")
        result = n.normalize(v)
        assert result.raw_value == "john@test.com"

    def test_phone_normalizer(self):
        from app.normalizers import PhoneNormalizer
        n = PhoneNormalizer()
        v = ExtractedValue(field_name=FieldName.PHONE, raw_value="555.123.4567",
                           source_type=SourceType.RESUME, extraction_method="regex")
        result = n.normalize(v)
        assert result.raw_value == "(555) 123-4567"

    def test_name_normalizer(self):
        from app.normalizers import NameNormalizer
        n = NameNormalizer()
        v = ExtractedValue(field_name=FieldName.FULL_NAME, raw_value="john  van  doe",
                           source_type=SourceType.RESUME, extraction_method="regex")
        result = n.normalize(v)
        assert result.raw_value == "John van Doe"

    def test_skills_normalizer_dedup(self):
        from app.normalizers import SkillsNormalizer
        n = SkillsNormalizer()
        v = ExtractedValue(field_name=FieldName.SKILLS, raw_value=["Python", "python", "Java"],
                           source_type=SourceType.RESUME, extraction_method="regex")
        result = n.normalize(v)
        assert len(result.raw_value) == 2  # Deduplicated


# ---- Fusion Tests ----

class TestFusion:
    def test_priority_based_single(self):
        from app.fusion import PriorityBasedFusionPolicy
        policy = PriorityBasedFusionPolicy()
        candidates = [
            ExtractedValue(field_name=FieldName.EMAIL, raw_value="a@test.com",
                           source_type=SourceType.RESUME, extraction_method="regex"),
        ]
        result = policy.fuse(FieldName.EMAIL, candidates, {"resume": 90})
        assert result.raw_value == "a@test.com"

    def test_priority_based_conflict(self):
        from app.fusion import PriorityBasedFusionPolicy
        policy = PriorityBasedFusionPolicy()
        candidates = [
            ExtractedValue(field_name=FieldName.EMAIL, raw_value="a@test.com",
                           source_type=SourceType.RESUME, extraction_method="regex"),
            ExtractedValue(field_name=FieldName.EMAIL, raw_value="b@test.com",
                           source_type=SourceType.ATS_JSON, extraction_method="field_mapping"),
        ]
        result = policy.fuse(FieldName.EMAIL, candidates, {"resume": 90, "ats_json": 80})
        assert result.raw_value == "a@test.com"  # Higher priority wins

    def test_list_merge(self):
        from app.fusion import ListMergeFusionPolicy
        policy = ListMergeFusionPolicy()
        candidates = [
            ExtractedValue(field_name=FieldName.SKILLS, raw_value=["Python", "Java"],
                           source_type=SourceType.RESUME, extraction_method="regex"),
            ExtractedValue(field_name=FieldName.SKILLS, raw_value=["Java", "Go"],
                           source_type=SourceType.GITHUB, extraction_method="repo_analysis"),
        ]
        result = policy.fuse(FieldName.SKILLS, candidates, {"resume": 90, "github": 70})
        assert "Python" in result.raw_value
        assert "Go" in result.raw_value
        # Java should not be duplicated
        assert result.raw_value.count("Java") == 1


# ---- Confidence Tests ----

class TestConfidence:
    def test_single_source_confidence(self):
        from app.confidence import DeterministicConfidenceEngine
        engine = DeterministicConfidenceEngine()
        selected = ExtractedValue(field_name=FieldName.EMAIL, raw_value="a@test.com",
                                  source_type=SourceType.RESUME, extraction_method="regex",
                                  extraction_confidence=0.95)
        score = engine.score(FieldName.EMAIL, selected, [selected], {"resume": 90})
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be reasonably confident with high-priority source

    def test_multi_source_agreement(self):
        from app.confidence import DeterministicConfidenceEngine
        engine = DeterministicConfidenceEngine()
        v1 = ExtractedValue(field_name=FieldName.EMAIL, raw_value="same@test.com",
                            source_type=SourceType.RESUME, extraction_method="regex",
                            extraction_confidence=0.95)
        v2 = ExtractedValue(field_name=FieldName.EMAIL, raw_value="same@test.com",
                            source_type=SourceType.ATS_JSON, extraction_method="field_mapping",
                            extraction_confidence=0.90)
        score = engine.score(FieldName.EMAIL, v1, [v1, v2], {"resume": 90, "ats_json": 80})
        assert score > 0.7  # Agreement should boost confidence


# ---- Confidence Level Tests ----

class TestConfidenceLevel:
    def test_from_score(self):
        assert ConfidenceLevel.from_score(0.9) == ConfidenceLevel.HIGH
        assert ConfidenceLevel.from_score(0.5) == ConfidenceLevel.MEDIUM
        assert ConfidenceLevel.from_score(0.3) == ConfidenceLevel.LOW
        assert ConfidenceLevel.from_score(0.1) == ConfidenceLevel.VERY_LOW


# ---- Projection Tests ----

class TestProjection:
    def test_include_fields(self):
        from app.projection import DefaultProjectionPolicy
        policy = DefaultProjectionPolicy()
        profile = CanonicalProfile(full_name="John", email="john@test.com", phone="555")
        config = ProjectionConfig(include_fields=["full_name", "email"])
        result = policy.project(profile, config)
        assert "full_name" in result
        assert "email" in result
        assert "phone" not in result

    def test_exclude_fields(self):
        from app.projection import DefaultProjectionPolicy
        policy = DefaultProjectionPolicy()
        profile = CanonicalProfile(full_name="John", email="john@test.com")
        config = ProjectionConfig(exclude_fields=["email"])
        result = policy.project(profile, config)
        assert "full_name" in result
        assert "email" not in result

    def test_rename_fields(self):
        from app.projection import DefaultProjectionPolicy
        policy = DefaultProjectionPolicy()
        profile = CanonicalProfile(full_name="John")
        config = ProjectionConfig(rename_fields={"full_name": "name"})
        result = policy.project(profile, config)
        assert "name" in result
        assert "full_name" not in result


# ---- Pipeline Integration Test ----

class TestPipeline:
    def test_full_pipeline(self):
        from app.factories import create_default_parser_factory
        from app.services.pipeline import SourceInput, TransformationPipeline

        factory = create_default_parser_factory(ocr_enabled=False)
        pipeline = TransformationPipeline(parser_factory=factory)

        # Create test sources
        ats_data = json.dumps({
            "name": "Jane Smith",
            "email": "jane@company.com",
            "phone": "555-867-5309",
            "title": "Senior Engineer",
            "company": "TechCorp",
            "skills": ["Python", "FastAPI", "PostgreSQL"],
        }).encode()

        github_data = json.dumps({
            "name": "Jane Smith",
            "login": "janesmith",
            "email": "jane@github.com",
            "bio": "Backend engineer passionate about APIs",
            "location": "San Francisco, CA",
            "company": "TechCorp",
            "repos": [
                {"language": "Python"}, {"language": "Go"}, {"language": "TypeScript"},
            ],
        }).encode()

        sources = [
            SourceInput(ats_data, "candidate_ats.json", SourceType.ATS_JSON),
            SourceInput(github_data, "github_profile.json", SourceType.GITHUB),
        ]

        record = pipeline.transform(sources)

        # Verify profile
        assert record.profile.full_name is not None
        assert "jane" in record.profile.email.lower()
        assert record.profile.current_company == "TechCorp"
        assert len(record.profile.skills) > 0

        # Verify metadata
        assert record.metadata.total_fields_extracted > 0
        assert record.metadata.overall_confidence > 0

        # Verify provenance
        assert len(record.provenance) > 0
        assert "email" in record.provenance
        email_prov = record.provenance["email"]
        assert email_prov.total_sources >= 1

    def test_pipeline_with_notes(self):
        from app.factories import create_default_parser_factory
        from app.services.pipeline import SourceInput, TransformationPipeline

        factory = create_default_parser_factory(ocr_enabled=False)
        pipeline = TransformationPipeline(parser_factory=factory)

        notes = b"Great candidate! jane@company.com has 8 years of experience in backend development."
        sources = [
            SourceInput(notes, "recruiter_notes.txt", SourceType.RECRUITER_NOTES),
        ]

        record = pipeline.transform(sources)
        assert record.profile.email == "jane@company.com"
        assert record.profile.years_of_experience == 8.0
