<?php

namespace App\Services;

use App\Models\Developer;
use App\Models\Metric;
use App\Models\Repository;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\DB;
use Exception;

class CollectorService
{
    public function __construct(
        protected GitHubService $gitHubService,
        protected WakaTimeService $wakaTimeService,
        protected ScoreCalculator $scoreCalculator
    ) {}

    public function syncDailyMetrics(Carbon $targetDate, bool $optimize = false, ?int $developerId = null, bool $syncGitHub = true, bool $syncWakaTime = true): array
    {
        $developers = $developerId
            ? Developer::where('id', $developerId)->get()
            : Developer::where('is_active', true)->get();

        $repositories = Repository::where('status', 'active')->get();
        $results = [];

        $isFullSync = ($syncGitHub && $syncWakaTime);
        $dateStr = $targetDate->toDateString();

        foreach ($developers as $dev) {
            $metric = Metric::where('developer_id', $dev->id)
                ->whereDate('date', $dateStr)
                ->first();

            if ($optimize && $metric && $metric->updated_at->toDateString() > $dateStr) {
                $results[] = ['developer' => $dev->name, 'status' => 'skipped'];
                continue;
            }

            if (!$optimize && $isFullSync && $metric) {
                $metric->delete();
                $metric = null;
            }

            $totalCommits = $metric->commits_count ?? 0;
            $linesAdded = $metric->lines_added ?? 0;
            $linesDeleted = $metric->lines_deleted ?? 0;
            $filesModified = $metric->files_modified ?? 0;
            $churnScore = $metric->churn_score ?? 0.0;
            $codingSeconds = $metric->coding_time_seconds ?? 0;
            $activeCodingSeconds = $metric->active_coding_seconds ?? 0;
            $deepWorkSeconds = $metric->deep_work_seconds ?? 0;
            $startWorkTime = $metric->start_work_time ?? null;
            $endWorkTime = $metric->end_work_time ?? null;
            $projectFocusRatio = $metric->project_focus_ratio ?? 0.0;
            $contextSwitches = $metric->context_switches ?? 0;
            $wakaTimeData = $metric->wakatime_data ?? null;

            try {
                DB::beginTransaction();

                if ($syncGitHub && $repositories->isNotEmpty()) {
                    $totalCommits = 0;
                    $linesAdded = 0;
                    $linesDeleted = 0;
                    $filesModified = 0;

                    foreach ($repositories as $repo) {
                        try {
                            $stats = $this->gitHubService->fetchCommitsInRepo($dev->git_username, $repo->name, $dateStr, $dateStr, $repo->token);
                            if ($repo->status === 'error') {
                                $repo->update(['status' => 'active', 'last_error' => null]);
                            }
                            $totalCommits += $stats['count'] ?? 0;
                            $linesAdded += $stats['lines_added'] ?? 0;
                            $linesDeleted += $stats['lines_deleted'] ?? 0;
                            $filesModified += $stats['files_modified'] ?? 0;
                        } catch (Exception $e) {
                            $repo->update(['status' => 'error', 'last_error' => $e->getMessage(), 'last_checked' => now()]);
                            \Log::warning("Repo {$repo->name} failed for {$dev->name}: " . $e->getMessage());
                            // Continue to next repo instead of failing the entire developer
                            continue;
                        }
                    }
                }

                $totalLines = $linesAdded + $linesDeleted;
                $churnScore = $totalLines > 0 ? round($linesDeleted / $totalLines, 2) : 0.0;

                if ($syncWakaTime && $dev->wakatime_api_key) {
                    $codingSeconds = $this->wakaTimeService->fetchCodingTime($dev->wakatime_api_key, $dateStr);
                    $wakaTimeData = $this->wakaTimeService->fetchDetailedSummary($dev->wakatime_api_key, $dateStr);
                    $durations = $this->wakaTimeService->fetchDurations($dev->wakatime_api_key, $dateStr);

                    if (!empty($durations)) {
                        $activeCodingSeconds = array_sum(array_column($durations, 'duration'));
                        usort($durations, fn($a, $b) => $a['time'] <=> $b['time']);
                        $minStart = $durations[0]['time'];
                        $maxEnd = 0;
                        foreach ($durations as $d) { $maxEnd = max($maxEnd, $d['time'] + $d['duration']); }
                        $startWorkTime = Carbon::createFromTimestamp($minStart);
                        $endWorkTime = Carbon::createFromTimestamp($maxEnd);

                        $deepWorkSeconds = 0;
                        $currentBlock = 0;
                        $lastEndTime = 0;
                        foreach ($durations as $d) {
                            if ($lastEndTime > 0 && ($d['time'] - $lastEndTime) <= 120) {
                                $currentBlock += ($d['duration'] + ($d['time'] - $lastEndTime));
                            } else {
                                if ($currentBlock >= 3600) { $deepWorkSeconds += $currentBlock; }
                                $currentBlock = $d['duration'];
                            }
                            $lastEndTime = $d['time'] + $d['duration'];
                        }
                        if ($currentBlock >= 3600) { $deepWorkSeconds += $currentBlock; }

                        $contextSwitches = 0;
                        $lastProject = null;
                        $projectTimes = [];
                        foreach ($durations as $d) {
                            $proj = $d['project'] ?? null;
                            if ($lastProject && $proj !== $lastProject) { $contextSwitches++; }
                            $lastProject = $proj;
                            $projectTimes[$proj] = ($projectTimes[$proj] ?? 0) + $d['duration'];
                        }
                        if ($activeCodingSeconds > 0 && !empty($projectTimes)) { $projectFocusRatio = round(max($projectTimes) / $activeCodingSeconds, 2); }
                    }
                }

                $score = $this->scoreCalculator->calculateDeveloperScore($totalCommits, $filesModified, $linesAdded, $linesDeleted, $churnScore, $activeCodingSeconds, $deepWorkSeconds, $projectFocusRatio, $contextSwitches);

                if ($startWorkTime && $endWorkTime && $startWorkTime->gt($endWorkTime)) { [$startWorkTime, $endWorkTime] = [$endWorkTime, $startWorkTime]; }

                // Delete existing metric if present, then create fresh
                Metric::where('developer_id', $dev->id)->whereDate('date', $dateStr)->delete();

                $metric = Metric::create(
                    ['developer_id' => $dev->id, 'date' => $dateStr, 'commits_count' => $totalCommits, 'lines_added' => $linesAdded, 'lines_deleted' => $linesDeleted, 'files_modified' => $filesModified, 'churn_score' => $churnScore, 'coding_time_seconds' => $codingSeconds, 'active_coding_seconds' => $activeCodingSeconds, 'deep_work_seconds' => $deepWorkSeconds, 'start_work_time' => $startWorkTime, 'end_work_time' => $endWorkTime, 'project_focus_ratio' => $projectFocusRatio, 'context_switches' => $contextSwitches, 'wakatime_data' => $wakaTimeData, 'score' => $score]
                );

                DB::commit();
                $results[] = ['developer' => $dev->name, 'date' => $dateStr, 'commits' => $totalCommits, 'coding_time' => floor($codingSeconds / 60) . ' mins', 'start' => $startWorkTime?->toIso8601String(), 'end' => $endWorkTime?->toIso8601String(), 'score' => $score];
            } catch (Exception $e) {
                DB::rollBack();
                \Log::error("Sync failed for {$dev->name} on {$dateStr}: " . $e->getMessage());
                $results[] = ['developer' => $dev->name, 'date' => $dateStr, 'status' => 'error', 'error' => $e->getMessage()];
                continue;
            }
        }
        return $results;
    }

    public function syncHistoricalData(int $days = 30, bool $additive = true): array
    {
        $today = now()->startOfDay();
        $startDate = $today->copy()->subDays($days);
        $results = [];
        for ($date = $startDate; $date->lte($today); $date->addDay()) {
            $dayResults = $this->syncDailyMetrics($date->copy(), $additive);
            $results = array_merge($results, $dayResults);
        }
        return $results;
    }
}
