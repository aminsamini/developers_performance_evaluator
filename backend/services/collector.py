from sqlalchemy.orm import Session
from datetime import date, timedelta, datetime
from ..models import Developer, Metric, Repository
from .git_service import GitService
from .wakatime_service import WakaTimeService
from .score_calculator import calculate_developer_score

async def sync_daily_metrics(db: Session, target_date: date, optimize: bool = False, developer_id: int | None = None):
    """
    Syncs metrics for developers for a SPECIFIC DATE.
    If developer_id is provided, only syncs that developer.
    If optimize=True, skips fetching for a developer if they already have >0 data for this date.
    """
    git_service = GitService()
    wakatime_service = WakaTimeService()
    
    if developer_id:
        developers = db.query(Developer).filter(Developer.id == developer_id).all()
        if not developers:
            print(f"Developer with ID {developer_id} not found.")
            return []
    else:
        developers = db.query(Developer).all()

    repositories = db.query(Repository).all()
    results = []

    print(f"--- Syncing metrics for {target_date} (Optimize={optimize}) ---")

    for dev in developers:
        # Check existing metric first - get ALL to handle potential duplicates
        existing_metrics = db.query(Metric).filter(
            Metric.developer_id == dev.id, 
            Metric.date == target_date
        ).all()
        
        # ALWAYS clean up duplicates if more than one exists (one-record-per-day rule)
        if len(existing_metrics) > 1:
            print(f"  [Cleanup] Found {len(existing_metrics)} records for {dev.name} on {target_date}, keeping newest")
            # Sort by id descending, keep the first (newest), delete the rest
            sorted_metrics = sorted(existing_metrics, key=lambda m: m.id, reverse=True)
            metric = sorted_metrics[0]
            for m in sorted_metrics[1:]:
                db.delete(m)
            db.commit()
            existing_metrics = [metric]  # Update list to reflect cleanup
        else:
            metric = existing_metrics[0] if existing_metrics else None

        # Check if the existing data is "finalized"
        is_finalized = False
        if metric and metric.updated_at:
            is_finalized = (metric.updated_at.date() > target_date)

        # STRICT OPTIMIZATION Rule #1:
        if optimize and metric and is_finalized:
             print(f"  [Skipping] {dev.name} for {target_date} (Finalized & Strict Optimization)")
             # ... append results ...
             results.append({
                "developer": dev.name,
                "date": target_date.isoformat(),
                "commits": metric.commits_count,
                "coding_time": f"{metric.coding_time_seconds//60} mins",
                "start": metric.start_work_time,
                "end": metric.end_work_time,
                "score": metric.score
             })
             continue
        
        # For targeted sync (optimize=False), delete and recreate the record
        if not optimize and existing_metrics:
            print(f"  [Targeted Sync] Deleting existing record for {dev.name} on {target_date} to ensure clean rewrite.")
            for m in existing_metrics:
                db.delete(m)
            db.commit()
            metric = None
        
        # If not finalized, or optimizations off, or no record -> We proceed to fetch.
        
        try:
            # ATOMIC SYNC Rule #2:
            # "make a validation if the request... interrupt or not give whole data dont make a record"
            # We use local variables. We only write to DB at the end if ALL succeed.

            # --- 1. Git Commits ---
            total_commits = 0
            lines_added = 0
            lines_deleted = 0
            files_modified = 0
            
            if repositories:
                for repo in repositories:
                    # fetch_commits_in_repo now returns DICT `{count, lines_added, ...}`
                    stats = await git_service.fetch_commits_in_repo(dev.git_username, repo.name, target_date, target_date, token=repo.token)
                    
                    total_commits += stats.get('count', 0)
                    lines_added += stats.get('lines_added', 0)
                    lines_deleted += stats.get('lines_deleted', 0)
                    files_modified += stats.get('files_modified', 0)

            # Calculate Churn Score (Rework Ratio)
            # Formula: Deletions / (Additions + Deletions)
            # High churn logic: > 0.7 means mostly rewriting? 
            churn_score = 0.0
            total_lines = lines_added + lines_deleted
            if total_lines > 0:
                churn_score = round(lines_deleted / total_lines, 2)

            # --- 2. WakaTime Stats ---
            coding_seconds = 0
            # --- 2. WakaTime Stats ---
            coding_seconds = 0
            active_coding_seconds = 0
            deep_work_seconds = 0
            project_focus_ratio = 0.0
            context_switches = 0
            wakatime_json = None
            
            if dev.wakatime_api_key:
                # User Request: "Remove repo filter". We now track ALL time reported by WakaTime.
                # We no longer strictly match 'allowed_projects'.
                
                try:
                    # A. Fetch Grand Total (All Projects)
                    coding_seconds = await wakatime_service.fetch_coding_time(
                        dev.wakatime_api_key, 
                        target_date
                        # No allowed_projects passed -> returns grand_total
                    )
                    
                    print(f"DEBUG: Fetched WakaTime Grand Total for {dev.name}: {coding_seconds} seconds ({coding_seconds/60} mins)")

                    # B. Fetch Detailed Summary
                    summary = await wakatime_service.fetch_detailed_summary(dev.wakatime_api_key, target_date)
                    import json
                    wakatime_json = json.dumps(summary) if summary else None

                    # C. Fetch Durations for Deep Work & Context Switching
                    durations = await wakatime_service.fetch_durations(dev.wakatime_api_key, target_date)
                    
                    min_start_timestamp = None
                    max_end_timestamp = None

                    if durations:
                        # 1. Active Time (Sum of ALL durations)
                        # We use all durations provided by WakaTime for this day
                        active_coding_seconds = int(sum(d.get('duration', 0) for d in durations))
                        
                        # 2. Deep Work (Contiguous blocks > 60 mins)
                        current_block = 0
                        last_end_time = 0
                        
                        sorted_durations = sorted(durations, key=lambda x: x['time'])
                        
                        # Calculate Start/End Times
                        min_start_timestamp = sorted_durations[0]['time'] if sorted_durations else None
                        max_end_timestamp = max((d['time'] + d['duration'] for d in sorted_durations), default=None)
                        
                        for d in sorted_durations:
                            start_time = d['time']
                            duration = d['duration']
                            end_time = start_time + duration
                            
                            # Gap < 2 mins = same session
                            if last_end_time > 0 and (start_time - last_end_time) <= 120:
                                current_block += (duration + (start_time - last_end_time))
                            else:
                                if current_block >= 3600:
                                    deep_work_seconds += current_block
                                current_block = duration
                            
                            last_end_time = end_time
                        
                        if current_block >= 3600:
                            deep_work_seconds += current_block

                        # 4. Context Switching (Project Changes)
                        # We use ALL durations for this, to see if they switched to *untracked* projects too?
                        # Or just switches within tracked projects? Let's penalize ANY switch.
                        # But we only care about switches causing distraction.
                        # 3. Context Switching & Focus (Using ALL durations now)
                        last_project = None
                        sorted_durations = sorted(durations, key=lambda x: x['time'])
                        for d in sorted_durations:
                            proj = d.get('project')
                            if last_project and proj != last_project:
                                context_switches += 1
                            last_project = proj

                        # 4. Project Focus Ratio
                        if active_coding_seconds > 0:
                            project_times = {}
                            for d in durations:
                                p = d.get('project')
                                project_times[p] = project_times.get(p, 0) + d['duration']
                            if project_times:
                                top_project_time = max(project_times.values())
                                project_focus_ratio = round(top_project_time / active_coding_seconds, 2)

                except Exception as e:
                    print(f"Error fetching WakaTime for {dev.name}: {e}")
                    raise e # Re-raise to trigger Atomic Rollback logic
            
            # 3. Calculate Score using the extracted score calculator module
            # This fixes the bug where inactive days would show 50 points
            score = calculate_developer_score(
                commits=total_commits,
                files_modified=files_modified,
                lines_added=lines_added,
                lines_deleted=lines_deleted,
                churn_score=churn_score,
                active_coding_seconds=active_coding_seconds,
                deep_work_seconds=deep_work_seconds,
                project_focus_ratio=project_focus_ratio,
                context_switches=context_switches
            )
            
            # 4. Save/Update DB (Only reached if no exception raised above)
            if not metric:
                metric = Metric(developer_id=dev.id, date=target_date)
                db.add(metric)
            
            metric.commits_count = total_commits
            metric.lines_added = lines_added
            metric.lines_deleted = lines_deleted
            metric.files_modified = files_modified
            metric.churn_score = churn_score
            
            metric.coding_time_seconds = coding_seconds # Keep legacy total
            metric.active_coding_seconds = active_coding_seconds
            metric.deep_work_seconds = deep_work_seconds
            metric.project_focus_ratio = project_focus_ratio
            metric.context_switches = context_switches
            metric.wakatime_data = wakatime_json
            
            # Format Start/End Strings
            from ..utils import get_timezone
            from datetime import datetime
            tz = get_timezone()
            metric.start_work_time = datetime.fromtimestamp(min_start_timestamp, tz).strftime("%H:%M") if min_start_timestamp else None
            metric.end_work_time = datetime.fromtimestamp(max_end_timestamp, tz).strftime("%H:%M") if max_end_timestamp else None

            metric.score = score
            
            # Use timezone aware current time
            from ..utils import get_current_time
            metric.updated_at = get_current_time()
            
            db.commit()
            print(f"  [Saved] Metrics for {dev.name} on {target_date}")
            
            results.append({
                "developer": dev.name,
                "date": target_date.isoformat(),
                "commits": total_commits,
                "coding_time": f"{coding_seconds//60} mins",
                "start": metric.start_work_time,
                "end": metric.end_work_time,
                "score": metric.score
            })

        except Exception as e:
            print(f"  [Sync Failed] Skiling {dev.name} for {target_date} due to error: {e}")
            db.rollback() # Rollback changes for this specific developer/day
            # We do NOT add to results, effectively "not making a record" or reporting incomplete data.
            continue
        
    return results

async def sync_historical_data(db: Session, days: int = 30, additive: bool = True):
    """
    Sync historical data for the last N days.
    
    Args:
        additive: If True, only sync days that have NO existing records (skip days with data).
                  If False, re-sync all days regardless of existing data.
    """
    print(f"--- Starting Historical Sync (Last {days} days, Additive={additive}) ---")
    from ..utils import get_current_time
    today = get_current_time().date()
    start_date = today - timedelta(days=days)
    
    results = []
    current = start_date
    while current <= today:
        if additive:
            # Check if ANY records exist for this date (any developer)
            existing_count = db.query(Metric).filter(Metric.date == current).count()
            if existing_count > 0:
                print(f"  [Additive Skip] {current} already has {existing_count} records, skipping")
                current += timedelta(days=1)
                continue
        
        day_results = await sync_daily_metrics(db, current, optimize=additive)
        results.extend(day_results)
        current += timedelta(days=1)
    
    return results

from ..utils import get_current_time

async def collect_metrics_for_all_developers(db: Session):
    """
    Manual sync button handler.
    ADDITIVE SYNC: Only fetches data for days that don't have ANY records.
    Days with existing data are skipped entirely.
    """
    print("=== Manual Sync (Additive Mode) ===")
    # Sync last 7 days, but only for days missing data
    return await sync_historical_data(db, days=7, additive=True)


