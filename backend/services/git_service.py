import httpx
import os
from datetime import datetime, date, timedelta

class GitService:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    async def fetch_commits_in_repo(self, username: str, repo_name: str, since_date: date, until_date: date | None = None, token: str | None = None) -> int:
        """
        Fetches the number of commits by a user in a SPECIFIC repository within a date range.
        If 'token' is provided, it uses that instead of the default env token.
        """
        api_token = token if token else self.token
        
        if not api_token:
             print("Warning: GITHUB_TOKEN not set and no repo token provided.")
             return 0

        headers = {
            "Authorization": f"token {api_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        async with httpx.AsyncClient() as client:
            
            params = {
                "author": username,
                "since": since_date.isoformat(),
                "per_page": 100,
            }
            if until_date:
                next_day = until_date + timedelta(days=1)
                params["until"] = next_day.isoformat()
            
            # print(f"DEBUG GIT REQUEST: {repo_name} | {params}")
            try:
                response = await client.get(
                    f"{self.base_url}/repos/{repo_name}/commits", 
                    headers=headers, 
                    params=params
                )
                
                if response.status_code != 200:
                    print(f"Stats check failed: {response.status_code} {response.text}")
                    return 0

                data = response.json()
                return len(data)

            except httpx.HTTPError as e:
                print(f"GitHub API Error for {repo_name}: {e}")
                return 0

    async def validate_repo_token(self, repo_name: str, token: str) -> bool:
        """
        Validates if the provided token has access to the repository.
        Returns True if successful (200 OK), False otherwise.
        """
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        async with httpx.AsyncClient() as client:
            try:
                # Minimal check: Get Repository Details
                response = await client.get(
                    f"{self.base_url}/repos/{repo_name}", 
                    headers=headers
                )
                if response.status_code == 200:
                    return True
                else:
                    print(f"Token validation failed for {repo_name}: {response.status_code} {response.text}")
                    return False
            except Exception as e:
                print(f"Token validation error: {e}")
                return False

            except httpx.HTTPError as e:
                print(f"GitHub API Error for {repo_name}: {e}")
                return 0
