<?php

namespace App\Services;

class ScoreCalculator
{
    public function calculateDeveloperScore(
        int $commits,
        int $filesModified,
        int $linesAdded,
        int $linesDeleted,
        float $churnScore,
        int $activeCodingSeconds,
        int $deepWorkSeconds,
        float $projectFocusRatio,
        int $contextSwitches
    ): float {
        $hasWorkActivity = ($commits > 0 || $activeCodingSeconds > 0 || $filesModified > 0);

        if (!$hasWorkActivity) {
            return 0.0;
        }

        $pCommits = min($commits * 1.0, 10.0);
        $totalLines = $linesAdded + $linesDeleted;
        $pLines = min($totalLines / 50.0, 10.0);
        $pFiles = min($filesModified * 2.0, 20.0);
        $activeHours = $activeCodingSeconds / 3600.0;
        $pTime = min($activeHours * 2.5, 20.0);
        $pStability = max(1.0, 20.0 * (1.0 - $churnScore));
        $deepHours = $deepWorkSeconds / 3600.0;
        $pDeepWork = min($deepHours * 2.5, 10.0);

        if ($projectFocusRatio >= 0.9) {
            $pFocus = 10.0;
        } elseif ($projectFocusRatio >= 0.5) {
            $pFocus = ($projectFocusRatio - 0.5) * 25.0;
        } else {
            $pFocus = 0.0;
        }

        $totalScore = $pCommits + $pLines + $pFiles + $pTime + $pStability + $pDeepWork + $pFocus;
        return round(min($totalScore, 100.0), 1);
    }

    public function getScoreBreakdown(
        int $commits,
        int $filesModified,
        int $linesAdded,
        int $linesDeleted,
        float $churnScore,
        int $activeCodingSeconds,
        int $deepWorkSeconds,
        float $projectFocusRatio,
        int $contextSwitches
    ): array {
        $hasWorkActivity = ($commits > 0 || $activeCodingSeconds > 0 || $filesModified > 0);

        if (!$hasWorkActivity) {
            return [
                'total' => 0.0,
                'has_activity' => false,
                'components' => [],
            ];
        }

        $totalLines = $linesAdded + $linesDeleted;
        $activeHours = $activeCodingSeconds / 3600.0;
        $deepHours = $deepWorkSeconds / 3600.0;

        $pCommits = min($commits * 1.0, 10.0);
        $pLines = min($totalLines / 50.0, 10.0);
        $pFiles = min($filesModified * 2.0, 20.0);
        $pTime = min($activeHours * 2.5, 20.0);
        $pStability = max(1.0, 20.0 * (1.0 - $churnScore));
        $pDeepWork = min($deepHours * 2.5, 10.0);

        if ($projectFocusRatio >= 0.9) {
            $pFocus = 10.0;
        } elseif ($projectFocusRatio >= 0.5) {
            $pFocus = ($projectFocusRatio - 0.5) * 25.0;
        } else {
            $pFocus = 0.0;
        }

        $total = $pCommits + $pLines + $pFiles + $pTime + $pStability + $pDeepWork + $pFocus;

        return [
            'total' => round(min($total, 100.0), 1),
            'has_activity' => true,
            'components' => [
                'commits' => ['value' => $commits, 'points' => round($pCommits, 1), 'label' => 'Commits'],
                'lines_changed' => ['value' => $totalLines, 'points' => round($pLines, 1), 'label' => 'Lines Changed'],
                'files_modified' => ['value' => $filesModified, 'points' => round($pFiles, 1), 'label' => 'Files Modified'],
                'coding_time' => ['value' => round($activeHours, 1), 'points' => round($pTime, 1), 'label' => 'Coding Time'],
                'code_stability' => ['value' => round((1 - $churnScore) * 100, 0), 'points' => round($pStability, 1), 'label' => 'Code Stability'],
                'deep_work' => ['value' => round($deepHours, 1), 'points' => round($pDeepWork, 1), 'label' => 'Deep Work'],
                'project_focus' => ['value' => round($projectFocusRatio * 100, 0), 'points' => round($pFocus, 1), 'label' => 'Project Focus'],
            ],
        ];
    }
}
