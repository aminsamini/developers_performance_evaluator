from sqlalchemy.orm import Session
from datetime import date, timedelta
from ..models import Developer, Metric, Repository
from .git_service import GitService
from .wakatime_service import WakaTimeService

async def sync_daily_metrics(db: Session, target_date: date, optimize: bool = False):
    """
    Syncs metrics for all developers for a SPECIFIC DATE.
    If optimize=True, skips fetching for a developer if they already have >0 data for this date.
    """
    git_service = GitService()
    wakatime_service = WakaTimeService()
    
    developers = db.query(Developer).all()
    repositories = db.query(Repository).all()
    results = []

    print(f"--- Syncing metrics for {target_date} (Optimize={optimize}) ---")

    for dev in developers:
        # Check existing metric first
        metric = db.query(Metric).filter(
            Metric.developer_id == dev.id, 
            Metric.date == target_date
        ).first()

        # --- 1. Git Commits ---
        total_commits = 0
        should_fetch_git = True
        
        if optimize and metric and metric.commits_count > 0:
             print(f"  [Skipping Git] {dev.name} already has commit data for {target_date}")
             total_commits = metric.commits_count
             should_fetch_git = False
        
        if should_fetch_git:
            if repositories:
                for repo in repositories:
                    count = await git_service.fetch_commits_in_repo(dev.git_username, repo.name, target_date, target_date, token=repo.token)
                    total_commits += count

        # --- 2. WakaTime Stats ---
        coding_seconds = 0
        should_fetch_waka = True
        
        if optimize and metric and metric.coding_time_seconds > 0:
             # Just a log if you want, or silent
             # print(f"  [Skipping Waka] {dev.name} already has wakatime data")
             coding_seconds = metric.coding_time_seconds
             should_fetch_waka = False

        if should_fetch_waka and dev.wakatime_api_key:
            try:
                coding_seconds = await wakatime_service.fetch_coding_time(dev.wakatime_api_key, target_date)
            except Exception as e:
                print(f"Error fetching WakaTime for {dev.name}: {e}")
                # If fetch failed, keep 0 or fallback to existing? 
                # Better keep 0 so we retry next time if optimize=True/False logic holds.
                coding_seconds = 0
            
        # 3. Calculate Score
        score = (total_commits * 10) + ((coding_seconds / 3600) * 5)
        
        # 4. Save/Update DB
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
        is_today = (target_date == today)
        
        # Optimize if NOT today (Meaning: user wants full check for today, partial/smart for past)
        should_optimize = not is_today
        
        print(f"Checking data for {target_date}... (Optimize={should_optimize})")
        await sync_daily_metrics(db, target_date, optimize=should_optimize)

async def collect_metrics_for_all_developers(db: Session):
    """
    Wrapper for manual sync button (defaults to just today for speed, or maybe last 7 days?)
    Let's make manual sync do today + yesterday to be quick but accurate.
    """
    # For manual sync, let's just do TODAY.
    today = date.today()
    # User requested to update last 7 days on sync
    return await sync_historical_data(db, days=7)

