"""GitHub Parser."""

import json
from app.interfaces.parser import ParserInterface
from app.models.intermediate import ParsedDocument, SourceType

class GitHubParser(ParserInterface):
    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        return source_type == SourceType.GITHUB_PROFILE

    def parse(self, content: bytes | str, source_type: SourceType, filename: str) -> ParsedDocument:
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = {}
            
        profile = data.get("profile", {})
        repos = data.get("repos", [])
        
        structured = {
            "name": profile.get("name"),
            "login": profile.get("login"),
            "email": profile.get("email"),
            "bio": profile.get("bio"),
            "location": profile.get("location"),
            "company": profile.get("company"),
            "html_url": profile.get("html_url"),
            "languages": list(set([r.get("language") for r in repos if r.get("language")]))
        }
        
        return ParsedDocument(
            source_type=source_type,
            filename=filename,
            structured_data=structured
        )
