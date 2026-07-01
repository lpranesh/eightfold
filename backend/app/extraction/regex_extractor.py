"""Regex-based baseline extraction."""

import re
from typing import Any
from app.interfaces.extractor import ExtractorInterface
from app.models.intermediate import ExtractedCandidate, ExtractedValue, ParsedDocument, SourceType
from app.core.exceptions import ExtractionException


class RegexExtractor(ExtractorInterface):
    """Extracts information using Regular Expressions."""

    EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
    PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    YOE_RE = re.compile(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)", re.I)

    def supported_source_types(self) -> list[SourceType]:
        return [SourceType.RESUME_PDF]

    def extract(self, parsed: ParsedDocument) -> ExtractedCandidate:
        text = parsed.raw_text or ""
        values: list[ExtractedValue] = []
        
        try:
            # Email
            emails = self.EMAIL_RE.findall(text)
            if emails:
                for em in set(emails):
                    values.append(self._make_val("emails", em, parsed.source_type, 0.9))

            # Phone
            phones = self.PHONE_RE.findall(text)
            if phones:
                for ph in set(phones):
                    values.append(self._make_val("phones", ph, parsed.source_type, 0.8))

            # YOE
            yoe = self.YOE_RE.search(text)
            if yoe:
                values.append(self._make_val("years_of_experience", float(yoe.group(1)), parsed.source_type, 0.7))
                
            # Basic fallback for Title (look for common title patterns near start)
            title_match = re.search(r"(?i)\b(Software Engineer|Developer|Data Scientist|Manager|Director|Engineer)\b", text[:1000])
            if title_match:
                values.append(self._make_val("current_title", title_match.group(1), parsed.source_type, 0.5))
                
            # Basic fallback for Skills
            skill_keywords = ["Python", "Java", "C\+\+", "React", "Node\.js", "AWS", "SQL", "Docker", "Kubernetes", "TypeScript", "Machine Learning"]
            for skill in skill_keywords:
                if re.search(rf"(?i)\b{skill}\b", text):
                    values.append(self._make_val("skills", skill.replace("\\", ""), parsed.source_type, 0.6))
                    
            # Basic fallback for Company
            company_match = re.search(r"(?i)(?:at|for) ([A-Z][a-z0-9]+(?:\s+[A-Z][a-z0-9]+){0,2})\b", text)
            if company_match and company_match.group(1).lower() not in ["the", "this", "my"]:
                values.append(self._make_val("current_company", company_match.group(1), parsed.source_type, 0.4))

            # Summary (fallback to first block of text)
            if text:
                summary_text = text[:500].strip()
                values.append(self._make_val("summary", summary_text, parsed.source_type, 0.4))

            return ExtractedCandidate(source_type=parsed.source_type, values=values)
        except Exception as e:
            raise ExtractionException(f"Regex extraction failed: {e}")

    def _make_val(self, name: str, val: Any, st: SourceType, conf: float) -> ExtractedValue:
        return ExtractedValue(
            field_name=name,
            raw_value=val,
            source_type=st,
            extraction_method="regex",
            extraction_confidence=conf
        )
