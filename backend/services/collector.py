from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime
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

        # Check if the existing data is "finalized"
        # If updated_at exists and date() > target_date, it was updated AFTER the day closed.
        is_finalized = False
        if metric and metric.updated_at:
            is_finalized = (metric.updated_at.date() > target_date)

        # Optimization Logic:
        # If optimize=True, we WANT to skip.
        # But if it's NOT finalized (meaning partial sync during the day), we MUST fetch.
        # User Rule: "if updated_at == date check that date again" -> implies re-fetch if not finalized.
        
        force_fetch = False
        if optimize and metric and not is_finalized:
             print(f"  [Re-Checking] {dev.name} for {target_date} (Last update was partial/same-day)")
             force_fetch = True

        # --- 1. Git Commits ---
        total_commits = 0
        should_fetch_git = True
        
        # If optimization is allowed AND (data exists OR finalized) AND not forcing fetch
        if optimize and metric and not force_fetch:
            if metric.commits_count > 0:
                 print(f"  [Skipping Git] {dev.name} already has commit data for {target_date}")
                 total_commits = metric.commits_count
                 should_fetch_git = False
            # Else if 0, we fetch (default behavior) unless we want to trust finalized 0?
            # User said: "if each field has value more than 0 it will not check it again"
            # Implicitly, if 0, check again? But if finalized, maybe we shouldn't?
            # Let's start with safe approach: if 0, check again.
        
        if should_fetch_git:
            if repositories:
                for repo in repositories:
                    count = await git_service.fetch_commits_in_repo(dev.git_username, repo.name, target_date, target_date, token=repo.token)
                    total_commits += count

        # --- 2. WakaTime Stats ---
        coding_seconds = 0
        should_fetch_waka = True
        
        if optimize and metric and not force_fetch:
            if metric.coding_time_seconds > 0:
                 # print(f"  [Skipping Waka] {dev.name} already has wakatime data")
                 coding_seconds = metric.coding_time_seconds
                 should_fetch_waka = False

        if should_fetch_waka and dev.wakatime_api_key:
            try:
                coding_seconds = await wakatime_service.fetch_coding_time(dev.wakatime_api_key, target_date)
            except Exception as e:
                print(f"Error fetching WakaTime for {dev.name}: {e}")
                should_fetch_waka = False # Failed, so effectively "fetched" 0 or keep old?
                # If we have old data, keep it?
                if metric: coding_seconds = metric.coding_time_seconds
                else: coding_seconds = 0
            
        # 3. Calculate Score
        score = (total_commits * 10) + ((coding_seconds / 3600) * 5)
        
        # 4. Save/Update DB
        if not metric:
            metric = Metric(developer_id=dev.id, date=target_date)
            db.add(metric)
        
        metric.commits_count = total_commits
        metric.coding_time_seconds = coding_seconds
        metric.score = round(score, 2)
        metric.updated_at = datetime.now() # Update timestamp!
        
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

