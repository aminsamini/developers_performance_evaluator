import asyncio
from backend.database import SessionLocal
from backend.models import Developer, Repository
from backend.services.git_service import GitService
import httpx

async def verify_usernames():
    db = SessionLocal()
    developers = db.query(Developer).all()
    repositories = db.query(Repository).all()
    git_service = GitService()

    with open("verify_result.txt", "w") as f:
        f.write(f"--- Verifying Usernames (DB vs Git) ---\n\n")
        
        # 1. List DB Developers
        print("Found DB developers:")
        db_usernames = {dev.git_username: dev for dev in developers}
        for dev in developers:
            msg = f"  [DB] Name: {dev.name} | GitUser: {dev.git_username}\n"
            print(msg.strip())
            f.write(msg)
        f.write("-" * 40 + "\n")

        # 2. Check Repositories
        for repo in repositories:
            msg = f"\nScanning Repo: {repo.name}...\n"
            print(msg.strip())
            f.write(msg)
            
            token = repo.token if repo.token else git_service.token
            if not token:
                msg = "  -> No token available. Skipping.\n"
                print(msg.strip())
                f.write(msg)
                continue

            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            url = f"https://api.github.com/repos/{repo.name}/commits"
            
            async with httpx.AsyncClient() as client:
                try:
                    # Fetch recent 50 commits
                    resp = await client.get(url, headers=headers, params={"per_page": 50})
                    if resp.status_code != 200:
                        msg = f"  -> API Error: {resp.status_code}\n"
                        print(msg.strip())
                        f.write(msg)
                        continue
                    
                    commits = resp.json()
                    found_authors = {}
                    
                    for c in commits:
                        github_author = c.get('author')
                        commit_author = c.get('commit', {}).get('author', {})
                        
                        if github_author:
                            login = github_author.get('login')
                            name = commit_author.get('name')
                            if login:
                                found_authors[login] = name
                    
                    if not found_authors:
                        msg = "  -> No GitHub users found in recent commits (maybe unlinked emails?)\n"
                        print(msg.strip())
                        f.write(msg)
                    else:
                        for login, name in found_authors.items():
                            status = "MATCH" if login in db_usernames else "MISSING IN DB"
                            msg = f"  -> Found Commit Author: {login} ({name}) => {status}\n"
                            print(msg.strip())
                            f.write(msg)

                except Exception as e:
                    msg = f"  -> Exception: {e}\n"
                    print(msg.strip())
                    f.write(msg)

    print("\n--- Verification Complete ---")
    db.close()

if __name__ == "__main__":
    asyncio.run(verify_usernames())
