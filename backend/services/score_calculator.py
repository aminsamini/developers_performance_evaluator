"""
Score Calculator Module
=======================
Implements a normalized 0-100 developer performance scoring system.

Scoring Components (Total 100 pts):
1. Commits (10 pts)
2. Lines Changed (10 pts)
3. Files Modified (20 pts)
4. Coding Time (20 pts)
5. Code Stability (20 pts)
6. Deep Work (10 pts)
7. Project Focus (10 pts)
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
    Calculate developer performance score (0-100).
    Returns 0 if no work activity is detected.
    """
    # === Zero Activity Rule ===
    has_work_activity = (
        commits > 0 or 
        active_coding_seconds > 0 or 
        files_modified > 0
    )
    
    if not has_work_activity:
        return 0.0
    
    # === 1. Commits (Max 10) ===
    # 1 point per commit, capped at 10
    p_commits = min(commits * 1.0, 10.0)
    
    # === 2. Lines Changed (Max 10) ===
    # 1 point per 50 lines, capped at 10
    total_lines = lines_added + lines_deleted
    p_lines = min(total_lines / 50.0, 10.0)
    
    # === 3. Files Modified (Max 20) ===
    # 2 points per file, capped at 20
    p_files = min(files_modified * 2.0, 20.0)
    
    # === 4. Coding Time (Max 20) ===
    # 2.5 points per hour, capped at 20 (8 hours)
    active_hours = active_coding_seconds / 3600.0
    p_time = min(active_hours * 2.5, 20.0)
    
    # === 5. Code Stability (Max 20) ===
    # Based on churn: max(1, 20 * (1 - churn))
    # range 1-20
    p_stability = max(1.0, 20.0 * (1.0 - churn_score))
    
    # === 6. Deep Work (Max 10) ===
    # 2.5 points per hour, capped at 10 (4 hours)
    deep_hours = deep_work_seconds / 3600.0
    p_deep_work = min(deep_hours * 2.5, 10.0)
    
    # === 7. Project Focus (Max 10) ===
    # >0.9: 10 pts, 0.5-0.9: scaled, <0.5: 0 pts
    if project_focus_ratio >= 0.9:
        p_focus = 10.0
    elif project_focus_ratio >= 0.5:
        p_focus = (project_focus_ratio - 0.5) * 25.0
    else:
        p_focus = 0.0
        
    total_score = p_commits + p_lines + p_files + p_time + p_stability + p_deep_work + p_focus
    
    # Final Cap at 100 just in case floating point logic overshoots (unlikely with min/max caps)
    return round(min(total_score, 100.0), 1)


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
    Get detailed breakdown for UI display.
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
        
    total_lines = lines_added + lines_deleted
    active_hours = active_coding_seconds / 3600.0
    deep_hours = deep_work_seconds / 3600.0
    
    # Logic repeats calculate_developer_score for components
    p_commits = min(commits * 1.0, 10.0)
    p_lines = min(total_lines / 50.0, 10.0)
    p_files = min(files_modified * 2.0, 20.0)
    p_time = min(active_hours * 2.5, 20.0)
    p_stability = max(1.0, 20.0 * (1.0 - churn_score))
    p_deep_work = min(deep_hours * 2.5, 10.0)
    
    if project_focus_ratio >= 0.9:
        p_focus = 10.0
    elif project_focus_ratio >= 0.5:
        p_focus = (project_focus_ratio - 0.5) * 25.0
    else:
        p_focus = 0.0
        
    total = p_commits + p_lines + p_files + p_time + p_stability + p_deep_work + p_focus
    
    return {
        "total": round(min(total, 100.0), 1),
        "has_activity": True,
        "components": {
            "commits": {"value": commits, "points": round(p_commits, 1), "label": "Commits"},
            "lines_changed": {"value": total_lines, "points": round(p_lines, 1), "label": "Lines Changed"},
            "files_modified": {"value": files_modified, "points": round(p_files, 1), "label": "Files Modified"},
            "coding_time": {"value": round(active_hours, 1), "points": round(p_time, 1), "label": "Coding Time"},
            "code_stability": {"value": round((1-churn_score)*100, 0), "points": round(p_stability, 1), "label": "Code Stability"},
            "deep_work": {"value": round(deep_hours, 1), "points": round(p_deep_work, 1), "label": "Deep Work"},
            "project_focus": {"value": round(project_focus_ratio*100, 0), "points": round(p_focus, 1), "label": "Project Focus"}
        }
    }
