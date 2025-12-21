# Developer Evaluation Logic

This document describes how the Performance Optimizer application calculates scores for developers.

## Scoring Formula

The daily score shifts focus from "Quantity" to "Quality" and "Stability".

### Formula
```
Score = (Commits * 1) + (Coding Hours * 10) + (Files Modified * 20) + (Lines Changed * 0.05) + ((1 - Churn) * 50)
```

### Components

### Components

1.  **Commits (Weight: 1)**
    *   **Logic**: Count of commits.
    *   **Impact**: **Lowest**. Each commit is worth only 1 point.

2.  **Files Modified (Weight: 20)**
    *   **Logic**: Number of unique files touched.
    *   **Impact**: **Highest**. Indicates the breadth and complexity of the task.

3.  **Lines Changed (Weight: 0.05)**
    *   **Logic**: Sum of Lines Added + Lines Deleted.
    *   **Impact**: **Volume Bonus**.

4.  **Stability Bonus (Weight: Up to 50)**
    *   **Logic**: `(1.0 - Churn Score)`. High Churn (Rework) reduces this bonus.

5.  **Enhanced Time Score (Composite)**
    *   **Active Coding**: **5 pts/hr**. Time spent actively typing/editing.
    *   **Deep Work**: **10 pts/hr**. Uninterrupted sessions > 1 hour.
    *   **Project Focus**: **Max 15 pts**. Ratio of time spent on primary project vs distractions.
    *   **Context Switching**: **-2 pts per switch**. Penalty for frequent task switching.
    *   *Formula*: `(ActiveHours * 5) + (DeepWorkHours * 10) + (FocusRatio * 15) - (Switches * 2)`

### Reliability & Verification

*   **Atomic Sync**: Data is only saved if *both* GitHub and WakaTime data are successfully retrieved. If an API failure or network interruption occurs during the fetch, the record for that day is **not updated**, preventing partial or incorrect zero values.
*   **Finalization**: Once a day has passed and data has been successfully synced (marked by `updated_at` > `date`), the system considers the record "Finalized".
*   **Optimization**: 
    *   **Finalized Records**: Are trusted and skipped in future syncs to save API rate limits.
    *   **Partial Records**: If a record was last updated on the *same day* (potentially incomplete), it is re-checked during the next sync to ensure all data is captured.
*   **Zero Values**: A zero value (0 commits, 0h time) is considered valid *only if* the sync completed successfully without errors.

## Example Calculation

**Developer**: Amin
**Date**: 2025-12-20
*   **Commits**: 3
*   **Coding Time**: 4 hours 30 minutes (4.5 hours)

**Score**:
*   Commit Score: `3 * 10 = 30`
*   Time Score: `4.5 * 5 = 22.5`
*   **Total Score**: `30 + 22.5 = 52.5`
