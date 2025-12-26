import asyncio
import os
from datetime import date, timedelta
from dotenv import load_dotenv
from backend.services.git_service import GitService

# Load env from backend/.env
load_dotenv("backend/.env")

async def test_git_service():
    service = GitService()
    token = os.getenv("GITHUB_TOKEN")
    print(f"Token present: {'Yes' if token else 'No'}")
    
    # ASK USER FOR INPUTS OR HARDCODE FOR TEST
    # We will try to fetch for a popular repo to verify logic if user didn't provide one, 
    # but we need a valid username for that repo.
    # Let's try to search for 'yyx990803' in 'vuejs/core' (Vue creator)
    
    username = "yyx990803"
    repo = "vuejs/core"
    
    # Look back 30 days
    since = date.today() - timedelta(days=30)
    
    print(f"Testing fetch for User: {username}, Repo: {repo}, Since: {since}")
    
    try:
        count = await service.fetch_commits_in_repo(username, repo, since)
        print(f"Result: {count} commits")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_git_service())
