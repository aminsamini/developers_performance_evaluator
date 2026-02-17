from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from typing import List
from . import models, database
from .services import collector
from .services.export_service import ExportService
from .routers import reports
from pydantic import BaseModel

class DeveloperCreate(BaseModel):
    name: str
    git_username: str
    wakatime_api_key: str | None = None

load_dotenv()

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
app.include_router(reports.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import asyncio

@app.on_event("startup")
async def startup_event():
    """
    App startup.
    1. Check DB schema for 'is_active' column in developers table and add if missing.
    2. Check DB schema for 'status' in repositories (already exists).
    """
    print("Performance Optimizer Backend started.")
    
    # Simple Migration Logic for SQLite
    try:
        from sqlalchemy import text
        with database.engine.connect() as conn:
            # Check if is_active exists in developers
            try:
                conn.execute(text("SELECT is_active FROM developers LIMIT 1"))
            except Exception:
                print("Migrating DB: Adding 'is_active' column to developers table.")
                conn.execute(text("ALTER TABLE developers ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                conn.commit()
    except Exception as e:
        print(f"Migration warning: {e}")

@app.get("/")
def read_root():
    return {"message": "Performance Optimizer Backend is running!"}

# --- DEVELOPERS ---

class DeveloperUpdate(BaseModel):
    name: str | None = None
    git_username: str | None = None
    wakatime_api_key: str | None = None

@app.post("/developers/")
def create_developer(developer: DeveloperCreate, db: Session = Depends(database.get_db)):
    try:
        db_dev = models.Developer(
            name=developer.name,
            git_username=developer.git_username,
            wakatime_api_key=developer.wakatime_api_key,
            is_active=True
        )
        db.add(db_dev)
        db.commit()
        return {"status": "created", "name": db_dev.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/developers/{developer_id}")
def update_developer(developer_id: int, update: DeveloperUpdate, db: Session = Depends(database.get_db)):
    dev = db.query(models.Developer).filter(models.Developer.id == developer_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Developer not found")
    
    if update.name is not None:
        dev.name = update.name
    if update.git_username is not None:
        dev.git_username = update.git_username
    if update.wakatime_api_key is not None:
        dev.wakatime_api_key = update.wakatime_api_key
        
    db.commit()
    return {"status": "updated", "developer": dev.name}

@app.delete("/developers/{developer_id}")
def deactivate_developer(developer_id: int, db: Session = Depends(database.get_db)):
    dev = db.query(models.Developer).filter(models.Developer.id == developer_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Developer not found")
    
    dev.is_active = False
    db.commit()
    return {"status": "deactivated", "developer": dev.name}

@app.post("/developers/{developer_id}/activate")
def activate_developer(developer_id: int, db: Session = Depends(database.get_db)):
    dev = db.query(models.Developer).filter(models.Developer.id == developer_id).first()
    if not dev:
        raise HTTPException(status_code=404, detail="Developer not found")
    
    dev.is_active = True
    db.commit()
    return {"status": "activated", "developer": dev.name}

@app.get("/developers/")
def get_developers(include_inactive: bool = False, db: Session = Depends(database.get_db)):
    query = db.query(models.Developer)
    if not include_inactive:
        query = query.filter(models.Developer.is_active == True)
    return query.all()


# --- REPOSITORIES ---

class RepositoryCreate(BaseModel):
    name: str # owner/repo
    token: str | None = None

@app.post("/repositories/")
async def create_repository(repo: RepositoryCreate, db: Session = Depends(database.get_db)):
    # Check if repo exists
    existing = db.query(models.Repository).filter(models.Repository.name == repo.name).first()
    if existing:
         # If existing but inactive, reactivate it?
         if existing.status == 'inactive':
             existing.status = 'active'
             if repo.token: # Update token if provided
                 existing.token = repo.token
             db.commit()
             return {"status": "reactivated", "name": existing.name}
         raise HTTPException(status_code=400, detail="Repository already exists")

    gs = collector.GitService()
    token_to_use = repo.token
    
    if token_to_use:
        is_valid = await gs.validate_repo_token(repo.name, token_to_use)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid GitHub Token or Repository not reachable.")
    
    db_repo = models.Repository(name=repo.name, token=repo.token, status='active')
    db.add(db_repo)
    db.commit()
    return {"status": "created", "name": db_repo.name}

@app.get("/repositories/")
def get_repositories(include_inactive: bool = False, db: Session = Depends(database.get_db)):
    query = db.query(models.Repository)
    if not include_inactive:
        query = query.filter(models.Repository.status != 'inactive')
    return query.all()

@app.delete("/repositories/{repo_id}")
def deactivate_repository(repo_id: int, db: Session = Depends(database.get_db)):
    repo = db.query(models.Repository).filter(models.Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    repo.status = 'inactive'
    db.commit()
    return {"status": "deactivated", "name": repo.name}

@app.post("/repositories/{repo_id}/activate")
def activate_repository(repo_id: int, db: Session = Depends(database.get_db)):
    repo = db.query(models.Repository).filter(models.Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    repo.status = 'active'
    db.commit()
    return {"status": "activated", "name": repo.name}
class TokenUpdate(BaseModel):
    token: str

@app.put("/repositories/{repo_id}/token")
async def update_repo_token(repo_id: int, update: TokenUpdate, db: Session = Depends(database.get_db)):
    repo = db.query(models.Repository).filter(models.Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Validate New Token
    gs = collector.GitService()
    is_valid = await gs.validate_repo_token(repo.name, update.token)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid Token or Repository not reachable")
    
    # Update DB
    repo.token = update.token
    repo.status = 'active'
    repo.last_error = None
    from datetime import datetime
    repo.last_checked = datetime.now()
    
    db.commit()
    return {"status": "success", "message": "Token updated and verified"}

class TargetedSyncRequest(BaseModel):
    developer_id: int | None = None
    date_from: str | None = None # "YYYY-MM-DD"
    date_to: str | None = None   # "YYYY-MM-DD"
    sync_github: bool = True
    sync_wakatime: bool = True

@app.post("/sync/target")
async def sync_targeted_metrics(request: TargetedSyncRequest, db: Session = Depends(database.get_db)):
    from datetime import date as date_obj
    from datetime import datetime, timedelta
    
    # Default to today if no dates provided
    start_date = date_obj.today()
    end_date = date_obj.today()

    if request.date_from:
        try:
             start_date = datetime.strptime(request.date_from, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD")
            
    if request.date_to:
        try:
             end_date = datetime.strptime(request.date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")
    
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="date_to must be after or equal to date_from")

    print(f"Received Targeted Sync Request: DevID={request.developer_id}, Range={start_date} to {end_date}")
    
    total_results = []
    current_date = start_date
    
    while current_date <= end_date:
        print(f"Syncing date: {current_date}")
        day_results = await collector.sync_daily_metrics(
            db, 
            current_date, 
            optimize=False, 
            developer_id=request.developer_id,
            sync_github=request.sync_github,
            sync_wakatime=request.sync_wakatime
        )
        total_results.extend(day_results)
        current_date += timedelta(days=1)

    return {"status": "success", "results": total_results}


@app.post("/sync")
async def sync_metrics(db: Session = Depends(database.get_db)):
    results = await collector.collect_metrics_for_all_developers(db)
    return {"status": "success", "results": results}

@app.get("/metrics/")
def get_metrics(
    page: int = 1, 
    per_page: int = 7, 
    developer_id: int = None,
    date_from: str = None,
    date_to: str = None,
    score_min: float = None,
    score_max: float = None,
    db: Session = Depends(database.get_db)
):
    """
    Fetch historical metrics with pagination and optional filters.
    - developer_id: Filter by specific developer
    - date_from/date_to: Filter by date range (YYYY-MM-DD)
    - score_min/score_max: Filter by score range
    """
    from sqlalchemy import func
    from datetime import datetime
    
    # Build base query for unique dates
    date_query = db.query(models.Metric.date).distinct()
    
    # Apply developer filter if specified
    if developer_id:
        date_query = date_query.filter(models.Metric.developer_id == developer_id)
    
    # Apply date range filters
    if date_from:
        try:
            from_dt = datetime.strptime(date_from, "%Y-%m-%d").date()
            date_query = date_query.filter(models.Metric.date >= from_dt)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_dt = datetime.strptime(date_to, "%Y-%m-%d").date()
            date_query = date_query.filter(models.Metric.date <= to_dt)
        except ValueError:
            pass
    
    # Apply score filters to date query
    if score_min is not None:
        date_query = date_query.filter(models.Metric.score >= score_min)
    if score_max is not None:
        date_query = date_query.filter(models.Metric.score <= score_max)
    
    # Get filtered unique dates (descending order)
    unique_dates = date_query.order_by(models.Metric.date.desc()).all()
    unique_dates = [d[0] for d in unique_dates]
    
    # Calculate pagination
    total_days = len(unique_dates)
    total_pages = max(1, (total_days + per_page - 1) // per_page)  # Ceiling division
    page = max(1, min(page, total_pages))  # Clamp page to valid range
    
    # Get dates for current page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_dates = unique_dates[start_idx:end_idx]
    
    if not page_dates:
        return {
            "data": [],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_days": total_days,
                "total_pages": total_pages
            }
        }
    
    # Build metrics query with filters
    metrics_query = db.query(models.Metric).join(models.Developer).filter(
        models.Metric.date.in_(page_dates)
    )
    
    if developer_id:
        metrics_query = metrics_query.filter(models.Metric.developer_id == developer_id)
    
    if score_min is not None:
        metrics_query = metrics_query.filter(models.Metric.score >= score_min)
    if score_max is not None:
        metrics_query = metrics_query.filter(models.Metric.score <= score_max)
    
    metrics = metrics_query.order_by(models.Metric.date.desc()).all()
    
    # Group by Date
    grouped = {}
    for m in metrics:
        d_str = m.date.isoformat()
        if d_str not in grouped:
            grouped[d_str] = []
        
        grouped[d_str].append({
            "developer": m.developer.name,
            "developer_id": m.developer_id,
            "commits": m.commits_count,
            "lines_added": m.lines_added,
            "lines_deleted": m.lines_deleted,
            "coding_time": f"{m.coding_time_seconds // 60} mins",
            "start": m.start_work_time,
            "end": m.end_work_time,
            "deep_work": f"{(m.deep_work_seconds or 0) // 60} mins",
            "focus_ratio": m.project_focus_ratio,
            "switches": m.context_switches,
            "score": m.score,
            "churn_score": m.churn_score,
            "details": m.wakatime_data
        })
    
    # Build result list sorted by date descending
    result_list = []
    for d_str in sorted(grouped.keys(), reverse=True):
        result_list.append({
            "date": d_str,
            "items": grouped[d_str]
        })
    
    return {
        "data": result_list,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_days": total_days,
            "total_pages": total_pages
        }
    }


@app.get("/metrics/detail/{developer_id}/{date_str}")
def get_metric_detail(developer_id: int, date_str: str, db: Session = Depends(database.get_db)):
    """
    Get detailed metrics for a specific developer on a specific date.
    Returns score breakdown and detailed work information.
    """
    from datetime import datetime
    from .services.score_calculator import get_score_breakdown
    
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get developer
    developer = db.query(models.Developer).filter(models.Developer.id == developer_id).first()
    if not developer:
        raise HTTPException(status_code=404, detail="Developer not found")
    
    # Get metric for that day
    metric = db.query(models.Metric).filter(
        models.Metric.developer_id == developer_id,
        models.Metric.date == target_date
    ).first()
    
    if not metric:
        raise HTTPException(status_code=404, detail="No metrics found for this date")
    
    # Get score breakdown
    breakdown = get_score_breakdown(
        commits=metric.commits_count or 0,
        files_modified=metric.files_modified or 0,
        lines_added=metric.lines_added or 0,
        lines_deleted=metric.lines_deleted or 0,
        churn_score=metric.churn_score or 0.0,
        active_coding_seconds=metric.active_coding_seconds or 0,
        deep_work_seconds=metric.deep_work_seconds or 0,
        project_focus_ratio=metric.project_focus_ratio or 0.0,
        context_switches=metric.context_switches or 0
    )
    
    # Parse wakatime data for charts
    wakatime_parsed = None
    if metric.wakatime_data:
        import json
        try:
            wakatime_parsed = json.loads(metric.wakatime_data)
        except:
            pass
    
    return {
        "developer": developer.name,
        "developer_id": developer_id,
        "date": date_str,
        "score": metric.score,
        "score_breakdown": breakdown,
        "metrics": {
            "commits": metric.commits_count,
            "lines_added": metric.lines_added,
            "lines_deleted": metric.lines_deleted,
            "files_modified": metric.files_modified,
            "churn_score": metric.churn_score,
            "coding_time_seconds": metric.coding_time_seconds,
            "active_coding_seconds": metric.active_coding_seconds,
            "deep_work_seconds": metric.deep_work_seconds,
            "start_time": metric.start_work_time,
            "end_time": metric.end_work_time,
            "focus_ratio": metric.project_focus_ratio,
            "context_switches": metric.context_switches
        },
        "wakatime_details": wakatime_parsed
    }


@app.get("/repositories")
def get_repositories(db: Session = Depends(database.get_db)):
    """Get all tracked repositories."""
    repos = db.query(models.Repository).all()
    return repos

@app.get("/metrics/summary")
def get_metrics_summary(
    days: int = 7, 
    developer_id: int = None, 
    date_from: str = None,
    date_to: str = None,
    db: Session = Depends(database.get_db)
):
    """
    Get aggregated metrics summary for dashboard charts.
    Returns data for performance trends and team overview.
    Now includes previous week data aligned by day of week for comparison.
    Supports specific date range filtering via date_from/date_to.
    """
    from datetime import date, timedelta, datetime
    from .utils import get_current_time
    from sqlalchemy import func
    
    today = get_current_time().date()
    
    # Determine Date Range
    if date_from and date_to:
        try:
             start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
             end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
             current_week_dates = []
             delta = (end_date - start_date).days
             for i in range(delta + 1):
                 current_week_dates.append(start_date + timedelta(days=i))
             
             # For comparison/trend in custom range, we might just look at the exact range
             # Previous period would be the same length immediately before
             prev_start = start_date - timedelta(days=delta + 1)
             prev_end = start_date - timedelta(days=1)
             prev_week_dates = []
             for i in range(delta + 1):
                 prev_week_dates.append(prev_start + timedelta(days=i))
                 
        except ValueError:
             # Fallback to default
             current_week_dates = [today - timedelta(days=i) for i in range(days-1, -1, -1)]
             prev_week_dates = [d - timedelta(days=days) for d in current_week_dates]
    else:
        # Calculate the last 7 days (today and 6 days before)
        current_week_dates = [today - timedelta(days=i) for i in range(days-1, -1, -1)]
        # Previous week: 7 days before current week
        prev_week_dates = [d - timedelta(days=days) for d in current_week_dates]
    
    # Weekday labels (short names)
    weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Build base query with optional developer filter
    base_query = db.query(models.Metric).join(models.Developer)
    if developer_id:
        base_query = base_query.filter(models.Metric.developer_id == developer_id)
    
    # Get all metrics in current range
    # Ensure current_week_dates is sorted for range validation
    sorted_dates = sorted(current_week_dates)
    if not sorted_dates: 
         sorted_dates = [today] # Fallback
         
    metrics = base_query.filter(
        models.Metric.date >= sorted_dates[0],
        models.Metric.date <= sorted_dates[-1]
    ).all()
    
    # Get previous week metrics
    prev_base_query = db.query(models.Metric).join(models.Developer)
    if developer_id:
        prev_base_query = prev_base_query.filter(models.Metric.developer_id == developer_id)
    
    prev_metrics = prev_base_query.filter(
        models.Metric.date >= prev_week_dates[0],
        models.Metric.date <= prev_week_dates[-1]
    ).all()
    
    # Daily totals for current week - indexed by date
    daily_data = {}
    developer_totals = {}
    
    for m in metrics:
        d_str = m.date.isoformat()
        dev_name = m.developer.name
        
        # Daily aggregation
        if d_str not in daily_data:
            daily_data[d_str] = {
                "total_score": 0, "total_commits": 0, "total_coding_mins": 0, "count": 0, 
                "date_obj": m.date,
                "items": [] # Store individual records for frontend breakdown
            }
        daily_data[d_str]["total_score"] += m.score or 0
        daily_data[d_str]["total_commits"] += m.commits_count or 0
        daily_data[d_str]["total_coding_mins"] += (m.coding_time_seconds or 0) // 60
        daily_data[d_str]["count"] += 1
        
        # Add item details
        daily_data[d_str]["items"].append({
            "developer_id": m.developer_id,
            "developer": dev_name, # Frontend expects "developer" or "name"? check usage. Frontend uses devId to map name or assumes it matches.
            "score": m.score or 0,
            "commits": m.commits_count or 0
        })
        
        # Developer aggregation
        if dev_name not in developer_totals:
            developer_totals[dev_name] = {"total_score": 0, "days_active": 0, "total_commits": 0, "developer_id": m.developer_id, "id": m.developer_id}
        developer_totals[dev_name]["total_score"] += m.score or 0
        developer_totals[dev_name]["total_commits"] += m.commits_count or 0
        if (m.commits_count or 0) > 0 or (m.active_coding_seconds or 0) > 0:
            developer_totals[dev_name]["days_active"] += 1
    
    # Previous week daily totals - indexed by date
    prev_daily_data = {}
    for m in prev_metrics:
        d_str = m.date.isoformat()
        if d_str not in prev_daily_data:
            prev_daily_data[d_str] = {"total_score": 0, "count": 0, "date_obj": m.date}
        prev_daily_data[d_str]["total_score"] += m.score or 0
        prev_daily_data[d_str]["count"] += 1
    
    # Build aligned arrays by day of week position
    trend_labels = []
    trend_scores = []
    trend_commits = []
    prev_trend_scores = []
    
    # Prepare flat daily_data list for response
    daily_data_list = []
    
    for i, curr_date in enumerate(current_week_dates):
        prev_date = prev_week_dates[i]
        
        # Label: "Mon 12/30" format
        weekday_label = weekday_names[curr_date.weekday()]
        label = f"{weekday_label} {curr_date.month}/{curr_date.day}"
        trend_labels.append(label)
        
        # Current week data
        curr_key = curr_date.isoformat()
        if curr_key in daily_data:
            trend_scores.append(round(daily_data[curr_key]["total_score"], 1))
            trend_commits.append(daily_data[curr_key]["total_commits"])
            # Add to list
            day_data = daily_data[curr_key].copy()
            day_data["date"] = curr_key
            del day_data["date_obj"] # Remove non-serializable
            daily_data_list.append(day_data)
        else:
            trend_scores.append(0)
            trend_commits.append(0)
            daily_data_list.append({
                "date": curr_key,
                "total_score": 0,
                "items": []
            })
        
        # Previous week data (aligned by same weekday position)
        prev_key = prev_date.isoformat()
        if prev_key in prev_daily_data:
            prev_trend_scores.append(round(prev_daily_data[prev_key]["total_score"], 1))
        else:
            prev_trend_scores.append(0)
    
    # Developer leaderboard
    leaderboard = [
        {"name": name, **data, "avg_score": round(data["total_score"] / max(data["days_active"], 1), 1)}
        for name, data in developer_totals.items()
    ]
    leaderboard.sort(key=lambda x: x["total_score"], reverse=True)
    
    # Calculate Best Day
    best_day = None
    if daily_data:
        # Find day with max score
        max_score_day = max(daily_data.values(), key=lambda x: x["total_score"])
        
        # Get details for that day
        d_obj = max_score_day["date_obj"]
        
        # Find top contributor for that day
        day_metrics = [m for m in metrics if m.date == d_obj]
        top_dev_name = "None"
        if day_metrics:
            top_dev_metric = max(day_metrics, key=lambda m: m.score or 0)
            top_dev_name = top_dev_metric.developer.name

        best_day = {
            "date": d_obj.isoformat(),
            "weekday": d_obj.strftime("%A"),
            "score": max_score_day["total_score"],
            "commits": max_score_day["total_commits"],
            "active_devs": max_score_day["count"],
            "top_contributor": top_dev_name
        }

    return {
        "trend": {
            "labels": trend_labels,
            "scores": trend_scores,
            "commits": trend_commits,
            "prev_scores": prev_trend_scores
        },
        "leaderboard": leaderboard,
        "best_day": best_day,
        "daily_data": daily_data_list, # Include detailed breakdowns
        "totals": {
            "total_score": sum(trend_scores),
            "total_commits": sum(trend_commits),
            "active_developers": len(developer_totals),
            "days_tracked": len([s for s in trend_scores if s > 0]),
            "repo_count": db.query(models.Repository).count()
        }
    }


class ExportRequest(BaseModel):
    from_date: str  # YYYY-MM-DD
    to_date: str    # YYYY-MM-DD
    developer_ids: List[int]
    format: str     # "excel" or "pdf"
    include_charts: bool = True
    include_summary: bool = True
    group_by_developer: bool = False
    include_raw_wakatime: bool = False

@app.post("/export/report")
async def export_report(request: ExportRequest, db: Session = Depends(database.get_db)):
    """
    Export performance report as Excel or PDF.
    Validates date range (max 90 days), fetches data, generates file.
    """
    from datetime import datetime, timedelta
    
    # Validate dates
    try:
        from_dt = datetime.strptime(request.from_date, "%Y-%m-%d").date()
        to_dt = datetime.strptime(request.to_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if to_dt < from_dt:
        raise HTTPException(status_code=400, detail="To date must be after or equal to from date")
    
    if (to_dt - from_dt).days > 90:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 90 days")
    
    if not request.developer_ids:
        raise HTTPException(status_code=400, detail="At least one developer must be selected")
    
    if request.format not in ["excel", "pdf"]:
        raise HTTPException(status_code=400, detail="Format must be 'excel' or 'pdf'")
    
    # Fetch metrics data
    metrics = db.query(models.Metric).filter(
        models.Metric.date >= from_dt,
        models.Metric.date <= to_dt,
        models.Metric.developer_id.in_(request.developer_ids)
    ).order_by(models.Metric.date.asc()).all()
    
    # Build developers map
    developers = db.query(models.Developer).filter(
        models.Developer.id.in_(request.developer_ids)
    ).all()
    developers_map = {d.id: d.name for d in developers}
    
    # Convert metrics to dict format
    metrics_data = []
    for m in metrics:
        metrics_data.append({
            "developer_id": m.developer_id,
            "date": m.date,
            "commits_count": m.commits_count,
            "lines_added": m.lines_added,
            "lines_deleted": m.lines_deleted,
            "files_modified": m.files_modified,
            "churn_score": m.churn_score,
            "coding_time_seconds": m.coding_time_seconds,
            "active_coding_seconds": m.active_coding_seconds,
            "deep_work_seconds": m.deep_work_seconds,
            "project_focus_ratio": m.project_focus_ratio,
            "context_switches": m.context_switches,
            "review_count": m.review_count,
            "start_work_time": m.start_work_time,
            "end_work_time": m.end_work_time,
            "score": m.score,
            "updated_at": m.updated_at,
            "wakatime_data": m.wakatime_data
        })
    
    # Generate export file
    export_service = ExportService()
    
    if request.format == "excel":
        file_buffer = export_service.generate_excel(
            metrics_data=metrics_data,
            developers_map=developers_map,
            from_date=request.from_date,
            to_date=request.to_date,
            include_charts=request.include_charts,
            include_summary=request.include_summary,
            group_by_developer=request.group_by_developer,
            include_raw_wakatime=request.include_raw_wakatime
        )
        filename = f"performance_report_{request.from_date}_to_{request.to_date}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        file_buffer = export_service.generate_pdf(
            metrics_data=metrics_data,
            developers_map=developers_map,
            from_date=request.from_date,
            to_date=request.to_date,
            include_charts=request.include_charts,
            include_summary=request.include_summary,
            group_by_developer=request.group_by_developer
        )
        filename = f"performance_report_{request.from_date}_to_{request.to_date}.pdf"
        media_type = "application/pdf"
    
    return StreamingResponse(
        file_buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
