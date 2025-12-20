from sqlalchemy.orm import Session
from datetime import date, timedelta
from ..models import Developer, Metric, Repository
from .git_service import GitService
from .wakatime_service import WakaTimeService

async def sync_daily_metrics(db: Session, target_date: date):
    """
    Syncs metrics for all developers for a SPECIFIC DATE.
    """
    git_service = GitService()
    wakatime_service = WakaTimeService()
    
    developers = db.query(Developer).all()
    repositories = db.query(Repository).all()
    results = []

    print(f"--- Syncing metrics for {target_date} ---")

    for dev in developers:
        # 1. Fetch Git Commits (for this specific day)
        total_commits = 0
        if repositories:
            for repo in repositories:
                # To get commits for ONE day, since=target, until=target
                count = await git_service.fetch_commits_in_repo(dev.git_username, repo.name, target_date, target_date, token=repo.token)
                total_commits += count
        
        # 2. Fetch WakaTime Stats
        coding_seconds = 0
        if dev.wakatime_api_key:
            coding_seconds = await wakatime_service.fetch_coding_time(dev.wakatime_api_key, target_date)
            
        # 3. Calculate Score
        score = (total_commits * 10) + ((coding_seconds / 3600) * 5)
        
        # 4. Save/Update DB
        metric = db.query(Metric).filter(
            Metric.developer_id == dev.id, 
            Metric.date == target_date
        ).first()
        
        if not metric:
            metric = Metric(developer_id=dev.id, date=target_date)
            db.add(metric)
        
        metric.commits_count = total_commits
        metric.coding_time_seconds = coding_seconds
        metric.score = round(score, 2)
        
        db.commit()
        results.append({
            "developer": dev.name,
            "date": target_date.isoformat(),
            "commits": total_commits,
            "coding_time": f"{coding_seconds//60} mins",
            "score": metric.score
        })
        
    return results

async def sync_historical_data(db: Session, days: int = 7):
    """
    Loops through the last N days (including today) and syncs data.
    """
    today = date.today()
    for i in range(days):
        target_date = today - timedelta(days=i)
        print(f"Checking data for {target_date}...")
        # Check if we already have fully populated data? 
        # For now, we just re-sync to be safe, or we could check if any metric exists.
        # Let's force sync for now to ensure consistency.
        await sync_daily_metrics(db, target_date)

async def collect_metrics_for_all_developers(db: Session):
    """
    Wrapper for manual sync button (defaults to just today for speed, or maybe last 7 days?)
    Let's make manual sync do today + yesterday to be quick but accurate.
    """
    # For manual sync, let's just do TODAY.
    today = date.today()
    return await sync_daily_metrics(db, today)

