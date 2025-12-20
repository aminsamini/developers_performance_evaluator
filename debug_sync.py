import asyncio
import os
from datetime import date, timedelta
from backend.database import SessionLocal
from backend.models import Developer, Repository, Metric
from backend.services.git_service import GitService

async def debug_sync_process():
    db = SessionLocal()
    developers = db.query(Developer).all()
    repositories = db.query(Repository).all()
    git_service = GitService()
    
    print(f"--- Debugging Sync Process ---")
    
    # 1. Check Repos and Tokens
    print(f"\n[1] Checking Repositories...")
    for repo in repositories:
        has_token = "YES" if repo.token else "NO (Uses Env Token)"
        print(f"  - Repo: {repo.name} | Has Token: {has_token}")
        if repo.token:
            print(f"    Token Preview: {repo.token[:10]}...")

    # 2. Simulate 7-Day Sync
    print(f"\n[2] Simulating Last 7 Days...")
    today = date.today()
    
    for i in range(7):
        target_date = today - timedelta(days=i)
        print(f"\n  === Date: {target_date} ===")
        
        for dev in developers:
            print(f"    Developer: {dev.name} ({dev.git_username})")
            
            total_commits_for_day = 0
            for repo in repositories:
                # Use the logic from collector.py
                token_to_use = repo.token
                
                # Fetch
                try:
                    count = await git_service.fetch_commits_in_repo(
                        dev.git_username, 
                        repo.name, 
                        target_date, 
                        target_date, 
                        token=token_to_use
                    )
                    print(f"      - Repo: {repo.name} -> {count} commits")
                    total_commits_for_day += count
                except Exception as e:
                    print(f"      - Repo: {repo.name} -> ERROR: {e}")
            
            print(f"    => Total for Day: {total_commits_for_day}")

    db.close()

if __name__ == "__main__":
    asyncio.run(debug_sync_process())
