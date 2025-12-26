import asyncio
from backend.services.wakatime_service import WakaTimeService
from backend.database import SessionLocal
from backend.models import Repository

def normalize(name):
    return name.lower().replace("_", "").replace("-", "").replace(" ", "")

def debug_matching():
    db = SessionLocal()
    repos = db.query(Repository).all()
    repo_names = [r.name for r in repos]
    
    allowed_projects = []
    for r in repos:
        allowed_projects.append(r.name) 
        if "/" in r.name:
            allowed_projects.append(r.name.split("/")[-1])
            
    normalized_allowed = [normalize(p) for p in allowed_projects]
    
    print("--- Debug Matching ---")
    print(f"Tracked Repositories: {repo_names}")
    print(f"Allowed Project Names (Raw): {allowed_projects}")
    print(f"Allowed Project Names (Norm): {normalized_allowed}")
    
    test_cases = ["Laravel-new-App", "laravel_new_app", "Octopus_Develop", "RandomProject"]
    
    for test in test_cases:
        norm_test = normalize(test)
        is_match = (test in allowed_projects or norm_test in normalized_allowed)
        print(f"Testing '{test}' (Norm: {norm_test}) -> Match: {is_match}")

    db.close()

if __name__ == "__main__":
    debug_matching()
