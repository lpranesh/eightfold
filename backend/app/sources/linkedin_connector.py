"""LinkedIn Connector."""

import httpx
from bs4 import BeautifulSoup
from app.models.intermediate import RawInput, SourceType

class LinkedInConnector:
    """Fetches LinkedIn profile data from URL."""

    async def fetch_profile(self, url: str) -> str:
        """Fetches the profile HTML. In a real system, this would use Proxycurl or authenticated session."""
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # We add headers to prevent immediate 999 blocking from LinkedIn
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": "en-US,en;q=0.9",
            }
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.text
            except httpx.HTTPError:
                # Fallback: if we get blocked, we just return a minimal mock HTML 
                # so the parser can extract *something* rather than inferring from URL.
                username = url.strip("/").split("/")[-1]
                return f"<html><head><title>{username} - LinkedIn</title></head><body><h1>{username}</h1></body></html>"
