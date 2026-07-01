"""Resume extractor — rule-based extraction from resume text."""

import logging
import re
from typing import Any, Optional

from app.exceptions import ExtractionException
from app.interfaces import ExtractorInterface
from app.models.domain.enums import FieldName, SourceType
from app.models.domain.source import ExtractedCandidate, ExtractedValue, ParsedDocument

logger = logging.getLogger(__name__)


class ResumeExtractor(ExtractorInterface):
    """Rule-based extractor for resume text using regex and positional heuristics."""

    SECTION_PATTERNS = {
        "experience": re.compile(r"(?:^|\n)\s*(?:work\s+)?experience\s*[\n:|-]", re.I),
        "education": re.compile(r"(?:^|\n)\s*education\s*[\n:|-]", re.I),
        "skills": re.compile(r"(?:^|\n)\s*(?:technical\s+)?skills?\s*[\n:|-]", re.I),
        "summary": re.compile(r"(?:^|\n)\s*(?:summary|objective|profile|about)\s*[\n:|-]", re.I),
        "certifications": re.compile(r"(?:^|\n)\s*certifications?\s*[\n:|-]", re.I),
    }

    EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
    PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?", re.I)
    GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+/?", re.I)
    URL_RE = re.compile(r"https?://(?:www\.)?[\w.-]+\.[a-zA-Z]{2,}(?:/\S*)?")

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.RESUME]

    def extract(self, parsed: ParsedDocument) -> ExtractedCandidate:
        if not parsed.raw_text:
            raise ExtractionException(message="No text content for extraction")

        text = parsed.raw_text
        values: list[ExtractedValue] = []
        warnings: list[str] = []

        self._extract_contact(text, values, warnings)
        sections = self._find_sections(text)
        self._extract_sections(text, sections, values, warnings)

        return ExtractedCandidate(source_type=SourceType.RESUME, values=values, extraction_warnings=warnings)

    def _extract_contact(self, text: str, values: list[ExtractedValue], warnings: list[str]) -> None:
        emails = self.EMAIL_RE.findall(text)
        if emails:
            values.append(ExtractedValue(field_name=FieldName.EMAIL, raw_value=emails[0].lower(),
                source_type=SourceType.RESUME, extraction_method="regex", extraction_confidence=0.95))

        phones = self.PHONE_RE.findall(text)
        if phones:
            values.append(ExtractedValue(field_name=FieldName.PHONE, raw_value=phones[0],
                source_type=SourceType.RESUME, extraction_method="regex", extraction_confidence=0.85))

        # Name: first non-empty, non-contact line
        for line in text.strip().split("\n")[:5]:
            line = line.strip()
            if not line or len(line) > 60:
                continue
            if self.EMAIL_RE.search(line) or self.PHONE_RE.search(line) or self.URL_RE.search(line):
                continue
            if any(p.search(line) for p in self.SECTION_PATTERNS.values()):
                continue
            values.append(ExtractedValue(field_name=FieldName.FULL_NAME, raw_value=line,
                source_type=SourceType.RESUME, extraction_method="positional_heuristic", extraction_confidence=0.75))
            parts = line.split()
            if len(parts) >= 2:
                values.append(ExtractedValue(field_name=FieldName.FIRST_NAME, raw_value=parts[0],
                    source_type=SourceType.RESUME, extraction_method="name_split", extraction_confidence=0.70))
                values.append(ExtractedValue(field_name=FieldName.LAST_NAME, raw_value=parts[-1],
                    source_type=SourceType.RESUME, extraction_method="name_split", extraction_confidence=0.70))
            break

        for pat, field in [(self.LINKEDIN_RE, FieldName.LINKEDIN_URL), (self.GITHUB_RE, FieldName.GITHUB_URL)]:
            matches = pat.findall(text)
            if matches:
                url = matches[0] if matches[0].startswith("http") else "https://" + matches[0]
                values.append(ExtractedValue(field_name=field, raw_value=url,
                    source_type=SourceType.RESUME, extraction_method="regex", extraction_confidence=0.95))

    def _find_sections(self, text: str) -> dict[str, tuple[int, int]]:
        found: list[tuple[str, int]] = []
        for name, pat in self.SECTION_PATTERNS.items():
            m = pat.search(text)
            if m:
                found.append((name, m.end()))
        found.sort(key=lambda x: x[1])
        result: dict[str, tuple[int, int]] = {}
        for i, (name, start) in enumerate(found):
            end = found[i + 1][1] if i + 1 < len(found) else len(text)
            result[name] = (start, end)
        return result

    def _extract_sections(self, text: str, sections: dict[str, tuple[int, int]],
                          values: list[ExtractedValue], warnings: list[str]) -> None:
        if "summary" in sections:
            s, e = sections["summary"]
            paras = [p.strip() for p in text[s:e].split("\n\n") if p.strip()]
            if paras:
                values.append(ExtractedValue(field_name=FieldName.SUMMARY, raw_value=paras[0],
                    source_type=SourceType.RESUME, extraction_method="section_extraction", extraction_confidence=0.80))

        if "skills" in sections:
            s, e = sections["skills"]
            st = text[s:e].strip()
            st = re.sub(r"[•●▪■◆►–-]\s*", ",", st)
            sep = "," if "," in st else ("|" if "|" in st else "\n")
            skills = [sk.strip() for sk in st.split(sep) if sk.strip() and len(sk.strip()) < 50]
            if skills:
                values.append(ExtractedValue(field_name=FieldName.SKILLS, raw_value=skills,
                    source_type=SourceType.RESUME, extraction_method="section_extraction", extraction_confidence=0.80))

        if "experience" in sections:
            s, e = sections["experience"]
            lines = [l.strip() for l in text[s:e].split("\n") if l.strip()][:6]
            at_re = re.compile(r"^(.+?)\s+(?:at|@)\s+(.+?)(?:\s*[|(]|$)", re.I)
            for line in lines:
                m = at_re.match(line)
                if m:
                    values.append(ExtractedValue(field_name=FieldName.CURRENT_TITLE, raw_value=m.group(1).strip(),
                        source_type=SourceType.RESUME, extraction_method="section_extraction", extraction_confidence=0.70))
                    values.append(ExtractedValue(field_name=FieldName.CURRENT_COMPANY, raw_value=m.group(2).strip(),
                        source_type=SourceType.RESUME, extraction_method="section_extraction", extraction_confidence=0.70))
                    break
