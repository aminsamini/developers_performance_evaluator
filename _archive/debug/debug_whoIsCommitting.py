import asyncio
import os
from backend.database import SessionLocal
from backend.models import Repository
from backend.services.git_service import GitService
import httpx

async def check_who_commits():
    db = SessionLocal()
    # Get the repo with the token
    repo = db.query(Repository).filter(Repository.token != None).first()
    
    if not repo:
        print("No repository with token found in DB.")
        repo = db.query(Repository).first() # Fallback
    
    if not repo:
        print("No repositories found.")
        return

    print(f"--- Debugging Commit Authors for Repo: {repo.name} ---")
    
    # Manually fetch commits without author filter
    git_service = GitService()
    token = repo.token if repo.token else git_service.token
    
    if not token:
        print("No token available.")
        return

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{repo.name}/commits"
    print(f"Fetching from: {url}")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, params={"per_page": 10})
            if resp.status_code != 200:
                print(f"Error: {resp.status_code} {resp.text}")
                return
            
            commits = resp.json()
            print(f"Found {len(commits)} recent commits.")
            
            with open("debug_authors.txt", "w") as f:
                for c in commits:
                    sha = c.get('sha', '')[:7]
                    commit_info = c.get('commit', {})
                    author_info = commit_info.get('author', {})
                    date_str = author_info.get('date', 'N/A')
                    github_author = c.get('author', {}) # This is the GitHub user object
                    
                    name = author_info.get('name', 'N/A')
                    email = author_info.get('email', 'N/A')
                    login = github_author.get('login', 'N/A') if github_author else "None (Unlinked Email?)"
                    
                    msg = f"Commit {sha} ({date_str}):\n  - Author Name: {name}\n  - Author Email: {email}\n  - GitHub Login: {login}\n-------------------------\n"
                    print(msg)
                    f.write(msg)
                
        except Exception as e:
            print(f"Request failed: {e}")
            
    db.close()

if __name__ == "__main__":
    asyncio.run(check_who_commits())
