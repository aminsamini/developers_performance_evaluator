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
        is_finalized = False
        if metric and metric.updated_at:
            is_finalized = (metric.updated_at.date() > target_date)

        # STRICT OPTIMIZATION Rule #1:
        # "if there is a record even if its 0 there is no need to check again, just check the date with the updated_at date"
        # Implication: If is_finalized is True, we TRUST the data (even if 0), so we SKIP.
        if optimize and metric and is_finalized:
             print(f"  [Skipping] {dev.name} for {target_date} (Finalized & Strict Optimization)")
             results.append({
                "developer": dev.name,
                "date": target_date.isoformat(),
                "commits": metric.commits_count,
                "coding_time": f"{metric.coding_time_seconds//60} mins",
                "score": metric.score
             })
             continue
        
        # If not finalized, or optimizations off, or no record -> We proceed to fetch.
        
        try:
            # ATOMIC SYNC Rule #2:
            # "make a validation if the request... interrupt or not give whole data dont make a record"
            # We use local variables. We only write to DB at the end if ALL succeed.

            # --- 1. Git Commits ---
            total_commits = 0
            if repositories:
                for repo in repositories:
                    # fetch_commits_in_repo now RAISES exception on error (modified in git_service.py)
                    count = await git_service.fetch_commits_in_repo(dev.git_username, repo.name, target_date, target_date, token=repo.token)
                    total_commits += count

            # --- 2. WakaTime Stats ---
            coding_seconds = 0
            # --- 2. WakaTime Stats ---
            coding_seconds = 0
            if dev.wakatime_api_key:
                # Prepare Allowed Projects List
                # User wants to filter only for "files which is on my repos".
                # WakaTime usually reports project name as the folder name (e.g., "performance_optimizer").
                # Our Repos are "aminsamiini-dev/performance_optimizer".
                # Strategy: Allow both full name AND the slug (part after the last slash).
                allowed_projects = []
                if repositories:
                    for r in repositories:
                        allowed_projects.append(r.name) # "owner/repo"
                        if "/" in r.name:
                            allowed_projects.append(r.name.split("/")[-1]) # "repo"
                
                try:
                    coding_seconds = await wakatime_service.fetch_coding_time(
                        dev.wakatime_api_key, 
                        target_date, 
                        allowed_projects=allowed_projects if allowed_projects else None
                    )
                except Exception as e:
                    print(f"Error fetching WakaTime for {dev.name}: {e}")
                    raise e # Re-raise to trigger Atomic Rollback logic
            
            # 3. Calculate Score
            score = (total_commits * 10) + ((coding_seconds / 3600) * 5)
            
            # 4. Save/Update DB (Only reached if no exception raised above)
            if not metric:
                metric = Metric(developer_id=dev.id, date=target_date)
                db.add(metric)
            
            metric.commits_count = total_commits
            metric.coding_time_seconds = coding_seconds
            metric.score = round(score, 2)
            metric.updated_at = datetime.now()
            
            db.commit() # Commit per developer/day (Atomic enough for this context)
            
            results.append({
                "developer": dev.name,
                "date": target_date.isoformat(),
                "commits": total_commits,
                "coding_time": f"{coding_seconds//60} mins",
                "score": metric.score
            })

        except Exception as e:
            print(f"  [Sync Failed] Skiling {dev.name} for {target_date} due to error: {e}")
            db.rollback() # Rollback changes for this specific developer/day
            # We do NOT add to results, effectively "not making a record" or reporting incomplete data.
            continue
        
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

