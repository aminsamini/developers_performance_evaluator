# Developer Performance Evaluation Logic

## Core Philosophy: High-Standard Normalized Scoring (0-100)
The scoring system is designed to evaluate developer productivity on a **normalized 0-100 scale**, based on high industry standards. It rewards deep work, complexity, and focus while penalizing churn and context switching.

**Zero Activity Rule:** If a developer has zero commits, zero coding time, and zero file changes, the score is automatically **0**.

### Score Interpretation Guide
| Score Range | Interpretation | Description |
|-------------|----------------|-------------|
| **0** | No Activity | No commits, coding time, or file changes detected. |
| **0 - 39** | Low Activity | Minimal contribution or mostly administrative day. |
| **40 - 60** | Standard | A typical productive day meeting baseline expectations. |
| **61 - 75** | Good | Above-average performance with solid contributions. |
| **76 - 89** | High Performance | Strong coding day with significant complexity or volume. |
| **90 - 100** | Exceptional | Top tier performance (rare, top 5% of days). |

---

## Score Components (Total: 100 Points)

The total score is the sum of 7 distinct components, each capped at a maximum value to prevent any single metric from skewing the result.

### 1. Commits (Max 10 Points)
*Encourages consistent, atomic contributions.*
- **Formula:** `min(commits, 10)`
- **Scale:** 1 point per commit.
- **Cap:** 10 commits = 10 points.

### 2. Lines Changed (Max 10 Points)
*Rewards volume of work (additions + deletions).*
- **Formula:** `min((additions + deletions) / 50, 10)`
- **Scale:** 1 point per 50 lines changed.
- **Cap:** 500+ lines = 10 points.

### 3. Files Modified (Max 20 Points) ⭐
*Indicates breadth and complexity of the task.*
- **Formula:** `min(files_modified * 2, 20)`
- **Scale:** 2 points per file modified.
- **Cap:** 10+ files = 20 points.

### 4. Coding Time (Max 20 Points) ⭐
*Measures active engagement with the codebase.*
- **Formula:** `min(active_hours * 2.5, 20)`
- **Scale:** 2.5 points per hour of active coding.
- **Cap:** 8+ hours = 20 points (Full standard work day).

### 5. Code Stability (Max 20 Points) ⭐
*Rewards clean code and low churn (writing code that stays).*
- **Formula:** `max(1, 20 * (1 - churn_ratio))`
- **Logic:**
    - **Low Churn (0-10%):** ~20 points (Clean new code)
    - **Medium Churn (50%):** 10 points (Refactoring/Iterating)
    - **High Churn (80%+):** ~1-4 points (Excessive rewriting)

### 6. Deep Work (Max 10 Points)
*Rewards long, uninterrupted coding sessions (≥ 90 mins).*
- **Formula:** `min(deep_work_hours * 2.5, 10)`
- **Scale:** 2.5 points per hour of deep work.
- **Cap:** 4+ hours = 10 points.

### 7. Project Focus (Max 10 Points)
*Penalizes context switching and rewards focus on a primary project.*
- **Formula:**
    - If Focus Ratio ≥ 90%: **10 points**
    - If Focus Ratio ≥ 50%: **Scaled linear** `(Ratio - 0.5) * 25`
    - If Focus Ratio < 50%: **0 points**

---

## Example Scenarios

### Scenario A: The "Standard Productive" Day
- **Activity:** 4 commits, 4 hours coding, 3 files touched, low churn.
- **Score:**
    - Commits: 4 pts
    - Lines (200): 4 pts
    - Files (3): 6 pts
    - Time (4h): 10 pts
    - Stability: 20 pts
    - Deep Work (1h): 2.5 pts
    - Focus (90%): 10 pts
    - **Total:** **56.5** (Standard)

### Scenario B: The "Heavy Lifter" Day
- **Activity:** 12 commits, 7 hours coding, 12 files touched, medium churn.
- **Score:**
    - Commits: 10 pts (capped)
    - Lines (1000): 10 pts (capped)
    - Files (12): 20 pts (capped)
    - Time (7h): 17.5 pts
    - Stability (30% churn): 14 pts
    - Deep Work (3h): 7.5 pts
    - Focus (95%): 10 pts
    - **Total:** **89** (Exceptional)

### Scenario C: The "Refactor" Day (High Churn)
- **Activity:** 2 commits, 5 hours coding, 2 files, 80% churn (deleting code).
- **Score:**
    - Commits: 2 pts
    - Lines (500): 10 pts
    - Files: 4 pts
    - Time: 12.5 pts
    - Stability (80% churn): 4 pts (High Penalty)
    - Deep Work: 5 pts
    - Focus: 10 pts
    - **Total:** **47.5** (Standard, lower due to churn)
