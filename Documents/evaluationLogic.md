# Developer Evaluation Logic

This document describes how the Performance Optimizer application calculates scores for developers.

## Scoring Formula

The daily score for each developer is calculated using a composite metric of **Code Commits** and **Coding Time**.

### Formula
```
Score = (Commits * 10) + (Coding Hours * 5)
```

### Components

1.  **Commits (Weight: 10)**
    *   **Source**: GitHub API
    *   **Logic**: The total number of commits pushed to *all* tracked repositories on that specific day.
    *   **Multiplier**: Each commit is worth **10 points**. 
    *   *Note*: Merges and pull requests count as commits if they appear in the commit history with the user's author email/username.

2.  **Coding Time (Weight: 5 per hour)**
    *   **Source**: WakaTime API
    *   **Logic**: The total time spent coding (in seconds) as tracked by the user's IDE plugin.
    *   **Calculation**: `(Total Seconds / 3600) * 5`
    *   **Effect**: Every hour of coding contributes **5 points**.

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
