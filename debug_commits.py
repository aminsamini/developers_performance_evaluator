import asyncio
import os
from datetime import date, timedelta
from backend.database import SessionLocal
from backend.models import Developer, Repository
from backend.services.git_service import GitService

# Force sync driver for this script if needed, or just use what's in env
# The service uses httpx (async), so we need asyncio.

async def debug_git_fetching():
    db = SessionLocal()
    developers = db.query(Developer).all()
    repositories = db.query(Repository).all()
    git_service = GitService()
    
    print(f"--- Debugging Data Collection ---")
    print(f"Found {len(developers)} Developers")
    print(f"Found {len(repositories)} Repositories")
    
    if not developers:
        print("ERROR: No developers found in DB.")
    if not repositories:
        print("ERROR: No repositories found in DB.")

    today = date.today()
    
    with open("debug_result.txt", "w") as f:
        for dev in developers:
            msg = f"\nDeveloper: {dev.name} (GitUser: {dev.git_username})\n"
            print(msg)
            f.write(msg)
            
            for repo in repositories:
                msg = f"  Checking Repo: {repo.name}...\n"
                print(msg.strip())
                f.write(msg)
                
                # Test 1: Check TODAY
                print(f"    [Test 1] Fetching for TODAY ({today})...")
                count_today = await git_service.fetch_commits_in_repo(dev.git_username, repo.name, today, today)
                msg = f"    -> Result: {count_today} commits\n"
                print(msg.strip())
                f.write(msg)
                
    db.close()

if __name__ == "__main__":
    asyncio.run(debug_git_fetching())
