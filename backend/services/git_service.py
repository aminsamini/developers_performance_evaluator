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

    async def fetch_commits_in_repo(self, username: str, repo_name: str, since_date: date, until_date: date | None = None, token: str | None = None) -> dict:
        """
        Fetches detailed stats for commits by a user in a repository within a date range.
        Returns: { 'count': int, 'lines_added': int, 'lines_deleted': int, 'files_modified': int }
        """
        api_token = token if token else self.token
        
        if not api_token:
             print("Warning: GITHUB_TOKEN not set and no repo token provided.")
             return {'count': 0, 'lines_added': 0, 'lines_deleted': 0, 'files_modified': 0}

        headers = {
            "Authorization": f"token {api_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        async with httpx.AsyncClient() as client:
            # Import get_timezone to handle User Timezone correctly
            from ..utils import get_timezone
            tz = get_timezone()
            
            # Construct Timezone-Aware Midnight
            # e.g. 2023-12-25 -> 2023-12-25 00:00:00+03:30
            # Use localize() for pytz timezones to handle clean offsets
            naive_since = datetime.combine(since_date, datetime.min.time())
            dt_since = tz.localize(naive_since)
            
            params = {
                "author": username,
                "since": dt_since.isoformat(),
                "per_page": 100,
            }
            if until_date:
                # End of the specific day (or start of next day in Local Time)
                naive_until = datetime.combine(until_date + timedelta(days=1), datetime.min.time())
                dt_until = tz.localize(naive_until)
                params["until"] = dt_until.isoformat()
            
            try:
                # 1. Get List of Commits (High Level)
                response = await client.get(
                    f"{self.base_url}/repos/{repo_name}/commits", 
                    headers=headers, 
                    params=params
                )
                
                if response.status_code != 200:
                    error_msg = f"GitHub API Error: {response.status_code} {response.text}"
                    print(error_msg)
                    raise Exception(error_msg)

                commits_list = response.json()
                
                total_stats = {
                    'count': len(commits_list),
                    'lines_added': 0,
                    'lines_deleted': 0,
                    'files_modified': 0
                }

                # 2. Fetch Details for Each Commit (Stats)
                print(f"  Fetching details for {len(commits_list)} commits in {repo_name}...")
                for commit in commits_list:
                    sha = commit['sha']
                    # Could potentially parallelize this with asyncio.gather, but keeping simple loop for reliability first.
                    detail_resp = await client.get(
                        f"{self.base_url}/repos/{repo_name}/commits/{sha}",
                        headers=headers
                    )
                    if detail_resp.status_code == 200:
                        detail = detail_resp.json()
                        stats = detail.get('stats', {'additions': 0, 'deletions': 0})
                        files = detail.get('files', [])
                        
                        total_stats['lines_added'] += stats['additions']
                        total_stats['lines_deleted'] += stats['deletions']
                        total_stats['files_modified'] += len(files)
                    else:
                        print(f"    Failed to fetch commit {sha}: {detail_resp.status_code}")

                return total_stats

            except httpx.HTTPError as e:
                print(f"GitHub API Connection Error for {repo_name}: {e}")
                raise e

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
