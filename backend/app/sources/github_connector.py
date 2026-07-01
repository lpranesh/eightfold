"""GitHub Connector."""

import json
import httpx
from typing import Any
from app.models.intermediate import SourceType

class GitHubConnector:
    """Fetches GitHub profile and repo data from URL using REST API."""

    async def fetch_profile(self, url: str) -> str:
        username = url.rstrip("/").split("/")[-1]
        
        async with httpx.AsyncClient() as client:
            headers = {"Accept": "application/vnd.github.v3+json"}
            
            # Fetch user profile
            user_resp = await client.get(f"https://api.github.com/users/{username}", headers=headers)
            user_data = user_resp.json() if user_resp.status_code == 200 else {}
            
            # Fetch repos for languages
            repos_resp = await client.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10", headers=headers)
            repos_data = repos_resp.json() if repos_resp.status_code == 200 else []
            
            # Combine
            combined = {
                "profile": user_data,
                "repos": repos_data
            }
            return json.dumps(combined)
