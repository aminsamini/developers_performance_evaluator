
def calculate_score(commits, lines_added, lines_deleted, files_modified, churn_score, active_seconds, deep_work_seconds, focus_ratio, switches):
    print(f"--- Debugging Score Calculation ---")
    print(f"Inputs: Commits={commits}, Churn={churn_score}, Active={active_seconds}, Deep={deep_work_seconds}")
    
    # Points for Commits
    p_commits = commits * 1
    print(f"p_commits: {p_commits}")

    # Enhanced Time Score
    active_hours = active_seconds / 3600
    deep_work_hours = deep_work_seconds / 3600
    
    p_active_time = active_hours * 5
    p_deep_work = deep_work_hours * 10
    p_focus = focus_ratio * 15
    p_switch_penalty = switches * 2
    
    p_time_score = max(0, p_active_time + p_deep_work + p_focus - p_switch_penalty)
    print(f"p_time_score: {p_time_score} (Active={p_active_time:.2f}, Deep={p_deep_work:.2f}, Focus={p_focus:.2f}, Penalty={p_switch_penalty})")

    # Points for Files 
    p_files = files_modified * 20
    print(f"p_files: {p_files}")
    
    # Points for Line Volume
    p_lines = (lines_added + lines_deleted) * 0.05
    print(f"p_lines: {p_lines}")
    
    # Points for Stability
    p_stability = (1.0 - churn_score) * 50
    print(f"p_stability: {p_stability} (Churn={churn_score})")
    
    score = p_commits + p_files + p_lines + p_stability + p_time_score
    print(f"TOTAL SCORE: {score}")
    return score

# User Data
# 1,1,2025-12-14,9,18620,0,0,...,1663,1660,46,0.5,18620,17382.479,0.95,18
# ID=1, Dev=1, Date=..., Commits=9, Coding=18620, LinesAdd=0, LinesDel=0, Files=1663, Churn=1660 ??
# Wait, if Files=1663, that usually means lines? Or 1663 files changed?
# 1663 files modified in 9 commits is HUGE.
# 1660 churn is HUGE.

calculate_score(
    commits=9, 
    lines_added=0, 
    lines_deleted=0, 
    files_modified=1663, 
    churn_score=1660, 
    active_seconds=18620, 
    deep_work_seconds=17382, 
    focus_ratio=0.95, 
    switches=18
)
