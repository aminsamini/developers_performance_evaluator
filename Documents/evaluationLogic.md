# Developer Evaluation Logic

This document describes how the Performance Optimizer application calculates scores for developers.

## Zero Activity Rule

> **IMPORTANT**: If a developer has no work activity for a day (0 commits, 0 coding time, 0 files modified), their score is **0**.

This prevents the "50-point inactive day" bug that previously occurred due to the stability bonus being awarded even when no work was done.

## Scoring Formula

The daily score focuses on **Quality**, **Stability**, and **Time Investment**.

### Formula
```
IF no_activity THEN
    Score = 0
ELSE
    Score = Commits + Files + Lines + Stability + TimeScore
```

Where:
- `Commits = count * 1`
- `Files = files_modified * 20`
- `Lines = (lines_added + lines_deleted) * 0.05`
- `Stability = (1.0 - churn_score) * 50`
- `TimeScore = max(0, ActiveTime + DeepWork + Focus - SwitchPenalty)`

### Score Components

| Component | Weight | Description |
|-----------|--------|-------------|
| Commits | 1 per commit | Low impact - encourages atomic commits |
| Files Modified | 20 per file | **Highest impact** - indicates task breadth/complexity |
| Lines Changed | 0.05 per line | Volume bonus for additions + deletions |
| Stability Bonus | Up to 50 | Low churn (rework) = higher bonus |
| Active Coding | 5 pts/hr | Time actively writing/editing code |
| Deep Work | 10 pts/hr | Uninterrupted sessions > 1 hour |
| Project Focus | Up to 15 | Ratio of time on primary project |
| Context Switches | -2 per switch | Penalty for frequent task switching |

### Churn Score Calculation
```
churn_score = lines_deleted / (lines_added + lines_deleted)
```
- High churn (>0.7) indicates mostly rewriting existing code
- Low churn (<0.3) indicates primarily new code

## Example Calculations

### Scenario 1: Day Off (No Activity)
| Metric | Value |
|--------|-------|
| Commits | 0 |
| Coding Time | 0h |
| Files Modified | 0 |
| **Score** | **0** |

*Zero activity = zero score. No stability bonus is awarded.*

### Scenario 2: Light Review Day
| Metric | Value | Points |
|--------|-------|--------|
| Commits | 1 | 1 × 1 = 1 |
| Files Modified | 2 | 2 × 20 = 40 |
| Lines Changed | 50 | 50 × 0.05 = 2.5 |
| Churn Score | 0.2 | (1-0.2) × 50 = 40 |
| Coding Time | 0.5h | 0.5 × 5 = 2.5 |
| **Total Score** | | **~86** |

### Scenario 3: Heavy Coding Day
| Metric | Value | Points |
|--------|-------|--------|
| Commits | 5 | 5 × 1 = 5 |
| Files Modified | 10 | 10 × 20 = 200 |
| Lines Changed | 800 | 800 × 0.05 = 40 |
| Churn Score | 0.1 | (1-0.1) × 50 = 45 |
| Active Coding | 6h | 6 × 5 = 30 |
| Deep Work | 4h | 4 × 10 = 40 |
| Focus Ratio | 0.9 | 0.9 × 15 = 13.5 |
| Switches | 3 | 3 × -2 = -6 |
| **Total Score** | | **~368** |

## Data Reliability & Verification

### Atomic Sync
- Data is only saved if **both** GitHub and WakaTime data are successfully retrieved
- API failures or network interruptions result in the record **not being updated**
- Prevents partial or incorrect zero values

### Finalization
- Once a day has passed and data is synced (marked by `updated_at > date`), the record is "Finalized"
- Finalized records are trusted and skipped in future syncs
- Partial records are re-checked during the next sync

### Zero Values
A zero value (0 commits, 0h time) is considered valid **only if** the sync completed successfully without errors.

## Industry Alignment

This scoring system aligns with industry best practices for developer productivity measurement:

1. **Quality over Quantity**: High weight on files modified, low weight on commits
2. **Deep Work Recognition**: Bonus for uninterrupted focus sessions
3. **Stability Reward**: Clean code with low churn is valued
4. **Context Switch Awareness**: Encourages focused work on fewer projects
5. **Transparent Calculation**: All components are visible and explainable
