from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import date, datetime, timedelta
import json
from .. import models, database

router = APIRouter(
    prefix="/reports",
    tags=["reports"]
)

class ReportRequest(BaseModel):
    from_date: str
    to_date: str
    developer_ids: Optional[List[int]] = None
    # Filters?

@router.post("/generate")
def generate_report(
    request: ReportRequest,
    db: Session = Depends(database.get_db)
):
    """
    Generates aggregated datasets for the Comprehensive Reports dashboard.
    Analyses WakaTime JSON blobs to produce detailed breakdowns.
    """
    try:
        start_date = datetime.strptime(request.from_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(request.to_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Fetch Metrics
    query = db.query(models.Metric).filter(
        models.Metric.date >= start_date,
        models.Metric.date <= end_date
    )
    
    if request.developer_ids:
        query = query.filter(models.Metric.developer_id.in_(request.developer_ids))
        
    metrics = query.all()
    
    # Aggregation Containers
    # 1. Time Series: { "2023-01-01": { time: 0, score: 0 } }
    time_series = {}
    
    # 2. Languages: { "Python": { time: 0, percent: 0 } }
    languages = {}
    
    # 3. Projects: { "ProjectA": { time: 0, percent: 0 } }
    projects = {}
    
    # 4. Editors: { "VS Code": { time: 0 } }
    editors = {}
    
    # 5. Operating Systems: { "Mac": { time: 0 } }
    operating_systems = {}
    
    # 6. Dependencies: { "React": { time: 0 } }
    dependencies = {}
    
    # 7. Categories: { "Coding": { time: 0 } }
    categories = {}
    
    # 8. Developer Stats
    developer_stats = {}
    
    total_seconds_global = 0

    for m in metrics:
        d_str = m.date.isoformat()
        
        # --- Time Series ---
        if d_str not in time_series:
            time_series[d_str] = {
                "date": d_str,
                "total_seconds": 0,
                "score": 0,
                "commits": 0,
                "human_additions": 0,
                "human_deletions": 0
            }
        
        time_series[d_str]["total_seconds"] += m.coding_time_seconds
        time_series[d_str]["score"] += m.score
        time_series[d_str]["commits"] += m.commits_count
        time_series[d_str]["human_additions"] += m.lines_added
        time_series[d_str]["human_deletions"] += m.lines_deleted
        
        total_seconds_global += m.coding_time_seconds

        # --- WakaTime JSON Parsing ---
        if m.wakatime_data:
            try:
                waka = json.loads(m.wakatime_data)
                
                # A. Languages
                for item in waka.get("languages", []):
                    name = item["name"]
                    sec = item["total_seconds"]
                    if name not in languages:
                        languages[name] = {"name": name, "total_seconds": 0}
                    languages[name]["total_seconds"] += sec
                    
                    # Daily Breakdown for Stacked Area Chart
                    if "languages" not in time_series[d_str]:
                        time_series[d_str]["languages"] = {}
                    if name not in time_series[d_str]["languages"]:
                        time_series[d_str]["languages"][name] = 0
                    time_series[d_str]["languages"][name] += sec

                # B. Projects
                for item in waka.get("projects", []):
                    name = item["name"]
                    sec = item["total_seconds"]
                    # Try to get line stats if available in WakaTime data (depends on plan/integration)
                    la = item.get("lines_added", 0)
                    ld = item.get("lines_deleted", 0)
                    
                    if name not in projects:
                        projects[name] = {
                            "name": name, 
                            "total_seconds": 0,
                            "lines_added": 0,
                            "lines_deleted": 0
                        }
                    projects[name]["total_seconds"] += sec
                    projects[name]["lines_added"] += la
                    projects[name]["lines_deleted"] += ld
                
                # C. Editors
                for item in waka.get("editors", []):
                    name = item["name"]
                    sec = item["total_seconds"]
                    if name not in editors:
                        editors[name] = {"name": name, "total_seconds": 0}
                    editors[name]["total_seconds"] += sec
                
                # D. Operating Systems
                for item in waka.get("operating_systems", []):
                    name = item["name"]
                    sec = item["total_seconds"]
                    if name not in operating_systems:
                        operating_systems[name] = {"name": name, "total_seconds": 0}
                    operating_systems[name]["total_seconds"] += sec
                
                # E. Dependencies (If available)
                for item in waka.get("dependencies", []):
                    name = item["name"]
                    sec = item["total_seconds"]
                    if name not in dependencies:
                        dependencies[name] = {"name": name, "total_seconds": 0}
                    dependencies[name]["total_seconds"] += sec

                # F. Categories (Coding, Debugging, etc.)
                for item in waka.get("categories", []):
                    name = item["name"]
                    sec = item["total_seconds"]
                    if name not in categories:
                        categories[name] = {"name": name, "total_seconds": 0}
                    categories[name]["total_seconds"] += sec
                
                # G. Developer Stats (For Team Charts)
                dev_name = m.developer.name
                if dev_name not in developer_stats:
                    developer_stats[dev_name] = {
                        "name": dev_name,
                        "total_seconds": 0,
                        "commits": 0,
                        "languages": {}
                    }
                
                developer_stats[dev_name]["total_seconds"] += m.coding_time_seconds
                developer_stats[dev_name]["commits"] += m.commits_count
                
                # Per-Dev Languages
                for item in waka.get("languages", []):
                    lname = item["name"]
                    lsec = item["total_seconds"]
                    if lname not in developer_stats[dev_name]["languages"]:
                        developer_stats[dev_name]["languages"][lname] = 0
                    developer_stats[dev_name]["languages"][lname] += lsec

            except json.JSONDecodeError:
                pass # Skip malformed JSON
    
    # Calculate Percentages
    def add_percent(container, global_total):
        res = []
        for key, val in container.items():
            if global_total > 0:
                val["percent"] = round((val["total_seconds"] / global_total) * 100, 2)
            else:
                val["percent"] = 0
            res.append(val)
        return sorted(res, key=lambda x: x["total_seconds"], reverse=True)
    
    # Process Developer Stats (Convert dict to list)
    developer_stats_list = []
    for dname, ddata in developer_stats.items():
        # Top 3 languages per dev
        sorted_langs = sorted(ddata["languages"].items(), key=lambda x: x[1], reverse=True)[:3]
        ddata["top_languages"] = [{"name": k, "seconds": v} for k, v in sorted_langs]
        del ddata["languages"] # Clean up heavy dict if needed, or keep? Keeping simplified "top_languages".
        developer_stats_list.append(ddata)
    
    developer_stats_list.sort(key=lambda x: x["total_seconds"], reverse=True)

    # Sort Time Series by Date
    time_series_list = sorted(time_series.values(), key=lambda x: x["date"])
    
    # Active Repos Count
    active_repos_count = db.query(models.Repository).filter(models.Repository.status == 'active').count()

    return {
        "time_series": time_series_list,
        "languages": add_percent(languages, total_seconds_global),
        "projects": add_percent(projects, total_seconds_global),
        "editors": add_percent(editors, total_seconds_global),
        "operating_systems": add_percent(operating_systems, total_seconds_global),
        "dependencies": add_percent(dependencies, total_seconds_global),
        "categories": add_percent(categories, total_seconds_global),
        "developer_stats": developer_stats_list,
        "totals": {
            "total_seconds": total_seconds_global,
            "total_hours": round(total_seconds_global / 3600, 1),
            "active_repos": active_repos_count
        }
    }
