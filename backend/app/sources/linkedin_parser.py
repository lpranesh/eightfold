"""LinkedIn Parser."""

from bs4 import BeautifulSoup
from app.interfaces.parser import ParserInterface
from app.models.intermediate import ParsedDocument, SourceType

class LinkedInParser(ParserInterface):
    def can_parse(self, source_type: SourceType, file_extension: str) -> bool:
        return source_type == SourceType.LINKEDIN_PROFILE

    def parse(self, content: bytes | str, source_type: SourceType, filename: str) -> ParsedDocument:
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Very rudimentary scraping for the assignment demonstration
        structured_data = {}
        
        # Try to extract name from title or h1
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text.split("-")[0].strip()
            if title_text:
                structured_data["full_name"] = title_text
                
        h1_tag = soup.find('h1')
        if h1_tag and not structured_data.get("full_name"):
            structured_data["full_name"] = h1_tag.text.strip()
            
        # Try to extract bio or summary from meta tags
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get("content"):
            structured_data["summary"] = meta_desc["content"]

        return ParsedDocument(
            source_type=source_type,
            filename=filename,
            raw_text=soup.get_text(separator=" ", strip=True),
            structured_data=structured_data
        )
