<?php

namespace App\Http\Controllers;

use App\Models\Metric;
use App\Models\Developer;
use App\Services\ScoreCalculator;
use Illuminate\Http\Request;
use Illuminate\Support\Carbon;

class MetricController extends Controller
{
    public function index(Request $request)
    {
        $page = (int)$request->query('page', 1);
        $perPage = (int)$request->query('per_page', 7);
        $developerId = $request->query('developer_id');
        $dateFrom = $request->query('date_from');
        $dateTo = $request->query('date_to');
        $scoreMin = $request->query('score_min');
        $scoreMax = $request->query('score_max');

        $query = Metric::query();

        if ($developerId) {
            $query->where('developer_id', $developerId);
        }

        if ($dateFrom) {
            $query->where('date', '>=', $dateFrom);
        }

        if ($dateTo) {
            $query->where('date', '<=', $dateTo);
        }

        if ($scoreMin !== null) {
            $query->where('score', '>=', $scoreMin);
        }

        if ($scoreMax !== null) {
            $query->where('score', '<=', $scoreMax);
        }

        // Get unique dates for pagination
        $uniqueDates = (clone $query)->distinct()->pluck('date')->sortDesc()->values();
        $totalDays = $uniqueDates->count();
        $totalPages = max(1, ceil($totalDays / $perPage));
        $page = max(1, min($page, $totalPages));

        $pageDates = $uniqueDates->forPage($page, $perPage);

        if ($pageDates->isEmpty()) {
            return response()->json([
                'data' => [],
                'pagination' => [
                    'page' => $page,
                    'per_page' => $perPage,
                    'total_days' => $totalDays,
                    'total_pages' => $totalPages,
                ]
            ]);
        }

        $metrics = Metric::with('developer')
            ->whereIn('date', $pageDates)
            ->when($developerId, fn($q) => $q->where('developer_id', $developerId))
            ->when($scoreMin !== null, fn($q) => $q->where('score', '>=', $scoreMin))
            ->when($scoreMax !== null, fn($q) => $q->where('score', '<=', $scoreMax))
            ->orderBy('date', 'desc')
            ->get();

        $grouped = $metrics->groupBy(fn($m) => $m->date->toDateString())->map(function ($dayMetrics, $date) {
            return [
                'date' => $date,
                'items' => $dayMetrics->map(function ($m) {
                    return [
                        'developer' => $m->developer->name,
                        'developer_id' => $m->developer_id,
                        'commits' => $m->commits_count,
                        'lines_added' => $m->lines_added,
                        'lines_deleted' => $m->lines_deleted,
                        'coding_time' => floor($m->coding_time_seconds / 60) . ' mins',
                        'start' => $m->start_work_time?->toIso8601String(),
                        'end' => $m->end_work_time?->toIso8601String(),
                        'deep_work' => floor(($m->deep_work_seconds ?? 0) / 60) . ' mins',
                        'focus_ratio' => $m->project_focus_ratio,
                        'switches' => $m->context_switches,
                        'score' => $m->score,
                        'churn_score' => $m->churn_score,
                        'details' => $m->wakatime_data,
                    ];
                })
            ];
        })->values();

        return response()->json([
            'data' => $grouped,
            'pagination' => [
                'page' => $page,
                'per_page' => $perPage,
                'total_days' => $totalDays,
                'total_pages' => $totalPages,
            ]
        ]);
    }

    public function show($developerId, $dateStr, ScoreCalculator $scoreCalculator)
    {
        $developer = Developer::findOrFail($developerId);
        $metric = Metric::where('developer_id', $developerId)
            ->where('date', $dateStr)
            ->firstOrFail();

        $breakdown = $scoreCalculator->getScoreBreakdown(
            $metric->commits_count ?? 0,
            $metric->files_modified ?? 0,
            $metric->lines_added ?? 0,
            $metric->lines_deleted ?? 0,
            $metric->churn_score ?? 0.0,
            $metric->active_coding_seconds ?? 0,
            $metric->deep_work_seconds ?? 0,
            $metric->project_focus_ratio ?? 0.0,
            $metric->context_switches ?? 0
        );

        return response()->json([
            'developer' => $developer->name,
            'developer_id' => $developerId,
            'date' => $dateStr,
            'score' => $metric->score,
            'score_breakdown' => $breakdown,
            'metrics' => [
                'commits' => $metric->commits_count,
                'lines_added' => $metric->lines_added,
                'lines_deleted' => $metric->lines_deleted,
                'files_modified' => $metric->files_modified,
                'churn_score' => $metric->churn_score,
                'coding_time_seconds' => $metric->coding_time_seconds,
                'active_coding_seconds' => $metric->active_coding_seconds,
                'deep_work_seconds' => $metric->deep_work_seconds,
                'start_time' => $metric->start_work_time?->toIso8601String(),
                'end_time' => $metric->end_work_time?->toIso8601String(),
                'focus_ratio' => $metric->project_focus_ratio,
                'context_switches' => $metric->context_switches,
            ],
            'wakatime_details' => $metric->wakatime_data,
        ]);
    }

    public function summary(Request $request)
    {
        $days = (int)$request->query('days', 7);
        $developerId = $request->query('developer_id');
        $dateFrom = $request->query('date_from');
        $dateTo = $request->query('date_to');

        $today = now()->startOfDay();

        if ($dateFrom && $dateTo) {
            $startDate = Carbon::parse($dateFrom);
            $endDate = Carbon::parse($dateTo);
            $delta = $startDate->diffInDays($endDate);

            $currentDates = [];
            for ($i = 0; $i <= $delta; $i++) {
                $currentDates[] = $startDate->copy()->addDays($i)->toDateString();
            }

            $prevStart = $startDate->copy()->subDays($delta + 1);
            $prevEnd = $startDate->copy()->subDay();
            $prevDates = [];
            for ($i = 0; $i <= $delta; $i++) {
                $prevDates[] = $prevStart->copy()->addDays($i)->toDateString();
            }
        } else {
            $currentDates = [];
            for ($i = $days - 1; $i >= 0; $i--) {
                $currentDates[] = $today->copy()->subDays($i)->toDateString();
            }
            $prevDates = array_map(fn($d) => Carbon::parse($d)->subDays($days)->toDateString(), $currentDates);
        }

        $query = Metric::with('developer')
            ->whereIn('date', $currentDates)
            ->when($developerId, fn($q) => $q->where('developer_id', $developerId));

        $metrics = $query->get();

        $prevMetrics = Metric::whereIn('date', $prevDates)
            ->when($developerId, fn($q) => $q->where('developer_id', $developerId))
            ->get();

        $dailyData = [];
        $developerTotals = [];

        foreach ($metrics as $m) {
            $dStr = $m.date->toDateString();
            $devName = $m->developer->name;

            if (!isset($dailyData[$dStr])) {
                $dailyData[$dStr] = ['total_score' => 0, 'total_commits' => 0, 'total_coding_mins' => 0, 'count' => 0, 'items' => []];
            }
            $dailyData[$dStr]['total_score'] += $m->score;
            $dailyData[$dStr]['total_commits'] += $m->commits_count;
            $dailyData[$dStr]['total_coding_mins'] += floor($m->coding_time_seconds / 60);
            $dailyData[$dStr]['count']++;
            $dailyData[$dStr]['items'][] = ['developer_id' => $m->developer_id, 'developer' => $devName, 'score' => $m->score, 'commits' => $m->commits_count];

            if (!isset($developerTotals[$devName])) {
                $developerTotals[$devName] = ['total_score' => 0, 'days_active' => 0, 'total_commits' => 0, 'developer_id' => $m->developer_id, 'id' => $m->developer_id];
            }
            $developerTotals[$devName]['total_score'] += $m->score;
            $developerTotals[$devName]['total_commits'] += $m->commits_count;
            if ($m->commits_count > 0 || $m->active_coding_seconds > 0) {
                $developerTotals[$devName]['days_active']++;
            }
        }

        $prevDailyData = $prevMetrics->groupBy(fn($m) => $m->date->toDateString())->map(fn($group) => ['total_score' => $group->sum('score')]);

        $trendLabels = [];
        $trendScores = [];
        $trendCommits = [];
        $prevTrendScores = [];
        $dailyDataList = [];

        foreach ($currentDates as $index => $currDateStr) {
            $currDate = Carbon::parse($currDateStr);
            $label = $currDate->format('D n/j');
            $trendLabels[] = $label;

            if (isset($dailyData[$currDateStr])) {
                $trendScores[] = round($dailyData[$currDateStr]['total_score'], 1);
                $trendCommits[] = $dailyData[$currDateStr]['total_commits'];
                $dayData = $dailyData[$currDateStr];
                $dayData['date'] = $currDateStr;
                $dailyDataList[] = $dayData;
            } else {
                $trendScores[] = 0;
                $trendCommits[] = 0;
                $dailyDataList[] = ['date' => $currDateStr, 'total_score' => 0, 'items' => []];
            }

            $prevDateStr = $prevDates[$index];
            $prevTrendScores[] = round($prevDailyData[$prevDateStr]['total_score'] ?? 0, 1);
        }

        $leaderboard = collect($developerTotals)->map(function ($data, $name) {
            return array_merge($data, [
                'name' => $name,
                'avg_score' => round($data['total_score'] / max($data['days_active'], 1), 1)
            ]);
        })->values()->sortByDesc('total_score')->values();

        $bestDay = null;
        if (!empty($dailyData)) {
            $maxScoreDayKey = collect($dailyData)->keys()->sortByDesc(fn($k) => $dailyData[$k]['total_score'])->first();
            $maxScoreDay = $dailyData[$maxScoreDayKey];
            $dObj = Carbon::parse($maxScoreDayKey);

            $dayMetrics = $metrics->where('date', $maxScoreDayKey);
            $topDev = $dayMetrics->sortByDesc('score')->first();

            $bestDay = [
                'date' => $maxScoreDayKey,
                'weekday' => $dObj->format('l'),
                'score' => $maxScoreDay['total_score'],
                'commits' => $maxScoreDay['total_commits'],
                'active_devs' => $maxScoreDay['count'],
                'top_contributor' => $topDev?->developer->name ?? 'None',
            ];
        }

        return response()->json([
            'trend' => [
                'labels' => $trendLabels,
                'scores' => $trendScores,
                'commits' => $trendCommits,
                'prev_scores' => $prevTrendScores,
            ],
            'leaderboard' => $leaderboard,
            'best_day' => $bestDay,
            'daily_data' => $dailyDataList,
            'totals' => [
                'total_score' => array_sum($trendScores),
                'total_commits' => array_sum($trendCommits),
                'active_developers' => count($developerTotals),
                'days_tracked' => count(array_filter($trendScores, fn($s) => $s > 0)),
                'repo_count' => \App\Models\Repository::count(),
            ]
        ]);
    }
}
