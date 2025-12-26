"""
Score Calculator Module
=======================
Extracted and corrected scoring logic for developer performance evaluation.

The key fix: Score should be 0 when there's no work activity (no commits, no coding time).
Previously, the stability bonus of 50 points was awarded even on inactive days.
"""


def calculate_developer_score(
    commits: int,
    files_modified: int,
    lines_added: int,
    lines_deleted: int,
    churn_score: float,
    active_coding_seconds: int,
    deep_work_seconds: int,
    project_focus_ratio: float,
    context_switches: int
) -> float:
    """
    Calculate developer performance score for a given day.
    
    Returns 0 if no work activity is detected (no commits AND no coding time AND no files modified).
    This fixes the bug where inactive days would show 50 points due to the stability bonus.
    
    Score Components:
    -----------------
    1. Commits (Weight: 1 per commit)
       - Low impact, encourages atomic commits
    
    2. Files Modified (Weight: 20 per file)
       - Highest impact - indicates breadth/complexity of work
    
    3. Lines Changed (Weight: 0.05 per line)
       - Volume bonus for additions + deletions
    
    4. Stability Bonus (Weight: up to 50)
       - Formula: (1.0 - churn_score) * 50
       - High churn (lots of deletions) reduces this bonus
       - ONLY awarded when work activity exists
    
    5. Time Score (Composite):
       - Active Coding: 5 pts/hr
       - Deep Work (>1hr sessions): 10 pts/hr  
       - Project Focus: up to 15 pts based on focus ratio
       - Context Switch Penalty: -2 pts per switch
    
    Args:
        commits: Number of commits for the day
        files_modified: Number of unique files touched
        lines_added: Total lines added
        lines_deleted: Total lines deleted
        churn_score: Ratio of deletions to total changes (0.0 - 1.0)
        active_coding_seconds: Total active coding time in seconds
        deep_work_seconds: Time spent in sessions > 1 hour
        project_focus_ratio: Ratio of time on primary project (0.0 - 1.0)
        context_switches: Number of project switches
        
    Returns:
        float: Total performance score (0 if no activity)
    """
    # === CRITICAL BUG FIX ===
    # Check for zero activity - don't award any points for days with no work
    has_work_activity = (
        commits > 0 or 
        active_coding_seconds > 0 or 
        files_modified > 0
    )
    
    if not has_work_activity:
        return 0.0
    
    # === Score Components (only calculated if work was done) ===
    
    # 1. Commit Score (low weight to discourage commit spam)
    p_commits = commits * 1
    
    # 2. Files Modified Score (high weight - indicates task complexity)
    p_files = files_modified * 20
    
    # 3. Line Volume Score
    p_lines = (lines_added + lines_deleted) * 0.05
    
    # 4. Stability Bonus (reward clean code with low churn)
    p_stability = (1.0 - churn_score) * 50
    
    # 5. Enhanced Time Score
    active_hours = active_coding_seconds / 3600
    deep_work_hours = deep_work_seconds / 3600
    
    p_active_time = active_hours * 5
    p_deep_work = deep_work_hours * 10
    p_focus = project_focus_ratio * 15
    p_switch_penalty = context_switches * 2
    
    # Time score can't go negative from penalties
    p_time_score = max(0, p_active_time + p_deep_work + p_focus - p_switch_penalty)
    
    # === Total Score ===
    total_score = p_commits + p_files + p_lines + p_stability + p_time_score
    
    return round(total_score, 2)


def get_score_breakdown(
    commits: int,
    files_modified: int,
    lines_added: int,
    lines_deleted: int,
    churn_score: float,
    active_coding_seconds: int,
    deep_work_seconds: int,
    project_focus_ratio: float,
    context_switches: int
) -> dict:
    """
    Get a detailed breakdown of score components for display in the UI.
    Useful for the detailed day view.
    
    Returns:
        dict: Breakdown of each score component
    """
    has_work_activity = (
        commits > 0 or 
        active_coding_seconds > 0 or 
        files_modified > 0
    )
    
    if not has_work_activity:
        return {
            "total": 0.0,
            "has_activity": False,
            "components": {}
        }
    
    active_hours = active_coding_seconds / 3600
    deep_work_hours = deep_work_seconds / 3600
    
    components = {
        "commits": {
            "value": commits,
            "points": commits * 1,
            "weight": 1
        },
        "files_modified": {
            "value": files_modified,
            "points": files_modified * 20,
            "weight": 20
        },
        "lines_changed": {
            "value": lines_added + lines_deleted,
            "points": (lines_added + lines_deleted) * 0.05,
            "weight": 0.05
        },
        "stability": {
            "value": round(1.0 - churn_score, 2),
            "points": (1.0 - churn_score) * 50,
            "weight": 50
        },
        "active_coding": {
            "value": round(active_hours, 2),
            "points": active_hours * 5,
            "weight": 5
        },
        "deep_work": {
            "value": round(deep_work_hours, 2),
            "points": deep_work_hours * 10,
            "weight": 10
        },
        "project_focus": {
            "value": project_focus_ratio,
            "points": project_focus_ratio * 15,
            "weight": 15
        },
        "context_switches": {
            "value": context_switches,
            "points": -context_switches * 2,
            "weight": -2
        }
    }
    
    # Calculate time sub-score
    time_score = max(0, 
        components["active_coding"]["points"] + 
        components["deep_work"]["points"] + 
        components["project_focus"]["points"] + 
        components["context_switches"]["points"]
    )
    
    total = (
        components["commits"]["points"] +
        components["files_modified"]["points"] +
        components["lines_changed"]["points"] +
        components["stability"]["points"] +
        time_score
    )
    
    return {
        "total": round(total, 2),
        "has_activity": True,
        "time_score": round(time_score, 2),
        "components": components
    }
