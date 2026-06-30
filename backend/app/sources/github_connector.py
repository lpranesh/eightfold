"""GitHub API Connector."""

import httpx
from pydantic import HttpUrl

from app.core.exceptions import ConnectorException


class GitHubConnector:
    """Retrieves profile information from GitHub URLs."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def fetch_profile(self, url: HttpUrl) -> bytes:
        """Fetch user profile data from GitHub API based on the URL."""
        url_str = str(url).rstrip("/")
        username = url_str.split("/")[-1]

        api_url = f"https://api.github.com/users/{username}"
        try:
            response = await self.client.get(
                api_url, 
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            response.raise_for_status()
            
            # Fetch repos for top languages
            repos_response = await self.client.get(
                f"{api_url}/repos?per_page=100&sort=updated",
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            
            data = response.json()
            if repos_response.status_code == 200:
                data["repos"] = repos_response.json()
                
            import json
            return json.dumps(data).encode("utf-8")
        except httpx.HTTPError as e:
            raise ConnectorException(f"Failed to fetch GitHub profile: {e}")
