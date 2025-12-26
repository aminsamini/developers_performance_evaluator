from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from . import models, database
from .services import collector
from pydantic import BaseModel

class DeveloperCreate(BaseModel):
    name: str
    git_username: str
    wakatime_api_key: str | None = None

load_dotenv()

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import asyncio

@app.on_event("startup")
async def startup_event():
    """
    Trigger automated 7-day sync in background on startup.
    """
    async def run_sync():
        print("Initiating startup background sync (Last 7 Days)...")
        db = database.SessionLocal()
        try:
            await collector.sync_historical_data(db, days=7)
            print("Startup sync completed.")
        except Exception as e:
            print(f"Startup sync failed: {e}")
        finally:
            db.close()

    asyncio.create_task(run_sync())

@app.get("/")
def read_root():
    return {"message": "Performance Optimizer Backend is running!"}

@app.post("/developers/")
def create_developer(developer: DeveloperCreate, db: Session = Depends(database.get_db)):
    print(f"Received request to create developer: {developer.name}")
    try:
        db_dev = models.Developer(
            name=developer.name,
            git_username=developer.git_username,
            wakatime_api_key=developer.wakatime_api_key
        )
        print("Adding to session...")
        db.add(db_dev)
        print("Committing...")
        db.commit()
        print("Committed successfully.")
        return {"status": "created", "name": db_dev.name}
    except Exception as e:
        print(f"Error creating developer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class RepositoryCreate(BaseModel):
    name: str # owner/repo
    token: str | None = None

@app.post("/repositories/")
async def create_repository(repo: RepositoryCreate, db: Session = Depends(database.get_db)):
    # Check if repo exists
    existing = db.query(models.Repository).filter(models.Repository.name == repo.name).first()
    if existing:
         raise HTTPException(status_code=400, detail="Repository already exists")

    # Validate Token if provided, or if backend has no default token? 
    # Logic: If token provided, validate it. If not, maybe validate with default token?
    # User requirement: "when someone add a repo git the token as well and check if the token works... if doesn't work pass an error."
    
    gs = collector.GitService()
    token_to_use = repo.token
    # If no token provided, we fall back to system token? Or require it?
    # For now, let's assume if provided we MUST validate.
    
    if token_to_use:
        is_valid = await gs.validate_repo_token(repo.name, token_to_use)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid GitHub Token or Repository not reachable.")
    
    # If not token provided, maybe we should try to validate with env token? 
    # Let's simple validate access in general.
    # But wait, GitService init reads env token.
    if not token_to_use:
         # Try with default
         is_valid = await gs.validate_repo_token(repo.name, gs.token) # gs.token comes from env
         if not is_valid:
             # Just a warning? Or block?
             # If it's public, it might work without token (but rate limits).
             # Let's enforce reachability.
             # Actually, validate_repo_token uses the passed token. passing gs.token checks system access.
             if not gs.token:
                  # If no system token and no repo token, we might strictly fail or allow public.
                  pass 
    
    db_repo = models.Repository(name=repo.name, token=repo.token)
    db.add(db_repo)
    db.commit()
    return {"status": "created", "name": db_repo.name}

@app.get("/repositories/")
def get_repositories(db: Session = Depends(database.get_db)):
    return db.query(models.Repository).all()


@app.get("/developers/")
def get_developers(db: Session = Depends(database.get_db)):
    return db.query(models.Developer).all()

class TargetedSyncRequest(BaseModel):
    developer_id: int | None = None
    date: str | None = None # "YYYY-MM-DD"

@app.post("/sync/target")
async def sync_targeted_metrics(request: TargetedSyncRequest, db: Session = Depends(database.get_db)):
    from datetime import date as date_obj
    from datetime import datetime
    
    target_date = date_obj.today()
    if request.date:
        try:
             target_date = datetime.strptime(request.date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
            
    print(f"Received Targeted Sync Request: DevID={request.developer_id}, Date={target_date}")
    
    results = await collector.sync_daily_metrics(db, target_date, optimize=False, developer_id=request.developer_id)
    return {"status": "success", "results": results}


@app.post("/sync")
async def sync_metrics(db: Session = Depends(database.get_db)):
    results = await collector.collect_metrics_for_all_developers(db)
    return {"status": "success", "results": results}

@app.get("/metrics/")
def get_metrics(days: int = 30, db: Session = Depends(database.get_db)):
    """
    Fetch historical metrics for the last N days.
    """
    from datetime import date, timedelta
    from .utils import get_current_time
    
    # Use timezone aware "today"
    since_date = get_current_time().date() - timedelta(days=days)
    
    # Fetch metrics joined with Developer info
    metrics = db.query(models.Metric).join(models.Developer).filter(
        models.Metric.date >= since_date
    ).order_by(models.Metric.date.desc()).all()
    
    # Group by Date
    grouped = {}
    for m in metrics:
        d_str = m.date.isoformat()
        if d_str not in grouped:
            grouped[d_str] = []
        
        grouped[d_str].append({
            "developer": m.developer.name,
            "commits": m.commits_count,
            "coding_time": f"{m.coding_time_seconds // 60} mins",
            "deep_work": f"{(m.deep_work_seconds or 0) // 60} mins",
            "focus_ratio": m.project_focus_ratio,
            "switches": m.context_switches,
            "score": m.score,
            "details": m.wakatime_data
        })
    
    # Return list of { date: "YYYY-MM-DD", items: [...] }
    result_list = []
    # Sort dates descending
    for d_str in sorted(grouped.keys(), reverse=True):
        result_list.append({
            "date": d_str,
            "items": grouped[d_str]
        })
        
    return result_list
