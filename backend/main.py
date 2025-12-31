from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from typing import List
from . import models, database
from .services import collector
from .services.export_service import ExportService
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
    App startup - NO auto-sync. Just load existing data.
    User must manually click "Sync Data" to fetch new data.
    """
    print("Performance Optimizer Backend started. No auto-sync - waiting for manual sync request.")

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


@app.get("/metrics/summary")
def get_metrics_summary(days: int = 7, db: Session = Depends(database.get_db)):
    """
    Get aggregated metrics summary for dashboard charts.
    Returns data for performance trends and team overview.
    Now includes previous week data for comparison.
    """
    from datetime import date, timedelta
    from .utils import get_current_time
    from sqlalchemy import func
    
    today = get_current_time().date()
    since_date = today - timedelta(days=days)
    prev_week_start = today - timedelta(days=days*2)
    prev_week_end = today - timedelta(days=days+1)
    
    # Get all metrics in current range
    metrics = db.query(models.Metric).join(models.Developer).filter(
        models.Metric.date >= since_date
    ).all()
    
    # Get previous week metrics
    prev_metrics = db.query(models.Metric).join(models.Developer).filter(
        models.Metric.date >= prev_week_start,
        models.Metric.date <= prev_week_end
    ).all()
    
    # Daily totals for current week trend chart
    daily_data = {}
    developer_totals = {}
    
    for m in metrics:
        d_str = m.date.isoformat()
        dev_name = m.developer.name
        
        # Daily aggregation
        if d_str not in daily_data:
            daily_data[d_str] = {"total_score": 0, "total_commits": 0, "total_coding_mins": 0, "count": 0}
        daily_data[d_str]["total_score"] += m.score or 0
        daily_data[d_str]["total_commits"] += m.commits_count or 0
        daily_data[d_str]["total_coding_mins"] += (m.coding_time_seconds or 0) // 60
        daily_data[d_str]["count"] += 1
        
        # Developer aggregation
        if dev_name not in developer_totals:
            developer_totals[dev_name] = {"total_score": 0, "days_active": 0, "total_commits": 0}
        developer_totals[dev_name]["total_score"] += m.score or 0
        developer_totals[dev_name]["total_commits"] += m.commits_count or 0
        if (m.commits_count or 0) > 0 or (m.active_coding_seconds or 0) > 0:
            developer_totals[dev_name]["days_active"] += 1
    
    # Previous week daily totals
    prev_daily_data = {}
    for m in prev_metrics:
        d_str = m.date.isoformat()
        if d_str not in prev_daily_data:
            prev_daily_data[d_str] = {"total_score": 0, "count": 0}
        prev_daily_data[d_str]["total_score"] += m.score or 0
        prev_daily_data[d_str]["count"] += 1
    
    # Format for charts - current week
    trend_labels = sorted(daily_data.keys())
    trend_scores = [round(daily_data[d]["total_score"], 1) for d in trend_labels]
    trend_commits = [daily_data[d]["total_commits"] for d in trend_labels]
    
    # Format previous week - align by day of week (same indices)
    prev_trend_labels = sorted(prev_daily_data.keys())
    prev_trend_scores = [round(prev_daily_data[d]["total_score"], 1) for d in prev_trend_labels]
    
    # Developer leaderboard
    leaderboard = [
        {"name": name, **data, "avg_score": round(data["total_score"] / max(data["days_active"], 1), 1)}
        for name, data in developer_totals.items()
    ]
    leaderboard.sort(key=lambda x: x["total_score"], reverse=True)
    
    return {
        "trend": {
            "labels": trend_labels,
            "scores": trend_scores,
            "commits": trend_commits,
            "prev_labels": prev_trend_labels,
            "prev_scores": prev_trend_scores
        },
        "leaderboard": leaderboard,
        "totals": {
            "total_score": sum(trend_scores),
            "total_commits": sum(trend_commits),
            "active_developers": len(developer_totals),
            "days_tracked": len(daily_data),
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
