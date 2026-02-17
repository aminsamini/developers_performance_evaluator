<?php

namespace App\Http\Controllers;

use App\Exports\MetricsExport;
use App\Models\Metric;
use App\Models\Developer;
use App\Models\Repository;
use Illuminate\Http\Request;
use Illuminate\Support\Carbon;
use Maatwebsite\Excel\Facades\Excel;
use Barryvdh\DomPDF\Facade\Pdf;

class ReportController extends Controller
{
    public function generate(Request $request)
    {
        $validated = $request->validate([
            'from_date' => 'required|date_format:Y-m-d',
            'to_date' => 'required|date_format:Y-m-d',
            'developer_ids' => 'nullable|array',
            'developer_ids.*' => 'integer',
        ]);

        $startDate = Carbon::parse($validated['from_date']);
        $endDate = Carbon::parse($validated['to_date']);

        $query = Metric::with('developer')
            ->where('date', '>=', $startDate->toDateString())
            ->where('date', '<=', $endDate->toDateString());

        if (!empty($validated['developer_ids'])) {
            $query->whereIn('developer_id', $validated['developer_ids']);
        }

        $metrics = $query->get();

        $timeSeries = [];
        $languages = [];
        $projects = [];
        $editors = [];
        $operatingSystems = [];
        $dependencies = [];
        $categories = [];
        $developerStats = [];
        $totalSecondsGlobal = 0;

        foreach ($metrics as $m) {
            $dStr = $m->date->toDateString();

            if (!isset($timeSeries[$dStr])) {
                $timeSeries[$dStr] = [
                    'date' => $dStr,
                    'total_seconds' => 0,
                    'score' => 0,
                    'commits' => 0,
                    'human_additions' => 0,
                    'human_deletions' => 0,
                    'languages' => [],
                ];
            }

            $timeSeries[$dStr]['total_seconds'] += $m->coding_time_seconds;
            $timeSeries[$dStr]['score'] += $m->score;
            $timeSeries[$dStr]['commits'] += $m->commits_count;
            $timeSeries[$dStr]['human_additions'] += $m->lines_added;
            $timeSeries[$dStr]['human_deletions'] += $m->lines_deleted;

            $totalSecondsGlobal += $m->coding_time_seconds;

            $waka = $m->wakatime_data;
            if ($waka) {
                // Languages
                foreach ($waka['languages'] ?? [] as $item) {
                    $name = $item['name'];
                    $sec = $item['total_seconds'];
                    if (!isset($languages[$name])) {
                        $languages[$name] = ['name' => $name, 'total_seconds' => 0];
                    }
                    $languages[$name]['total_seconds'] += $sec;

                    if (!isset($timeSeries[$dStr]['languages'][$name])) {
                        $timeSeries[$dStr]['languages'][$name] = 0;
                    }
                    $timeSeries[$dStr]['languages'][$name] += $sec;
                }

                // Projects
                foreach ($waka['projects'] ?? [] as $item) {
                    $name = $item['name'];
                    $sec = $item['total_seconds'];
                    $la = $item['lines_added'] ?? 0;
                    $ld = $item['lines_deleted'] ?? 0;

                    if (!isset($projects[$name])) {
                        $projects[$name] = ['name' => $name, 'total_seconds' => 0, 'lines_added' => 0, 'lines_deleted' => 0];
                    }
                    $projects[$name]['total_seconds'] += $sec;
                    $projects[$name]['lines_added'] += $la;
                    $projects[$name]['lines_deleted'] += $ld;
                }

                // Editors
                foreach ($waka['editors'] ?? [] as $item) {
                    $name = $item['name'];
                    $sec = $item['total_seconds'];
                    if (!isset($editors[$name])) {
                        $editors[$name] = ['name' => $name, 'total_seconds' => 0];
                    }
                    $editors[$name]['total_seconds'] += $sec;
                }

                // Developer Stats
                $devName = $m->developer->name;
                if (!isset($developerStats[$devName])) {
                    $developerStats[$devName] = [
                        'name' => $devName,
                        'total_seconds' => 0,
                        'commits' => 0,
                        'languages' => [],
                    ];
                }

                $developerStats[$devName]['total_seconds'] += $m->coding_time_seconds;
                $developerStats[$devName]['commits'] += $m->commits_count;

                foreach ($waka['languages'] ?? [] as $item) {
                    $lname = $item['name'];
                    $lsec = $item['total_seconds'];
                    $developerStats[$devName]['languages'][$lname] = ($developerStats[$devName]['languages'][$lname] ?? 0) + $lsec;
                }
            }
        }

        $addPercent = function ($container, $globalTotal) {
            $res = array_values($container);
            foreach ($res as &$val) {
                $val['percent'] = $globalTotal > 0 ? round(($val['total_seconds'] / $globalTotal) * 100, 2) : 0;
            }
            usort($res, fn($a, $b) => $b['total_seconds'] <=> $a['total_seconds']);
            return $res;
        };

        $developerStatsList = [];
        foreach ($developerStats as $dname => $ddata) {
            arsort($ddata['languages']);
            $topLangs = array_slice($ddata['languages'], 0, 3, true);
            $ddata['top_languages'] = [];
            foreach ($topLangs as $k => $v) {
                $ddata['top_languages'][] = ['name' => $k, 'seconds' => $v];
            }
            unset($ddata['languages']);
            $developerStatsList[] = $ddata;
        }
        usort($developerStatsList, fn($a, $b) => $b['total_seconds'] <=> $a['total_seconds']);

        $timeSeriesList = array_values($timeSeries);
        usort($timeSeriesList, fn($a, $b) => $a['date'] <=> $b['date']);

        $activeReposCount = Repository::where('status', 'active')->count();

        return response()->json([
            'time_series' => $timeSeriesList,
            'languages' => $addPercent($languages, $totalSecondsGlobal),
            'projects' => $addPercent($projects, $totalSecondsGlobal),
            'editors' => $addPercent($editors, $totalSecondsGlobal),
            'operating_systems' => $addPercent($operatingSystems, $totalSecondsGlobal),
            'dependencies' => $addPercent($dependencies, $totalSecondsGlobal),
            'categories' => $addPercent($categories, $totalSecondsGlobal),
            'developer_stats' => $developerStatsList,
            'totals' => [
                'total_seconds' => $totalSecondsGlobal,
                'total_hours' => round($totalSecondsGlobal / 3600, 1),
                'active_repos' => $activeReposCount,
            ]
        ]);
    }

    public function export(Request $request)
    {
        $validated = $request->validate([
            'from_date' => 'required|date_format:Y-m-d',
            'to_date' => 'required|date_format:Y-m-d',
            'developer_ids' => 'required|array',
            'developer_ids.*' => 'integer',
            'format' => 'required|in:excel,pdf',
        ]);

        $metrics = Metric::with('developer')
            ->where('date', '>=', $validated['from_date'])
            ->where('date', '<=', $validated['to_date'])
            ->whereIn('developer_id', $validated['developer_ids'])
            ->orderBy('date', 'asc')
            ->get();

        $filename = "performance_report_{$validated['from_date']}_to_{$validated['to_date']}";

        if ($request->format === 'excel') {
            return Excel::download(new MetricsExport($metrics), "{$filename}.xlsx");
        } else {
            $pdf = Pdf::loadView('reports.performance', [
                'metrics' => $metrics,
                'fromDate' => $validated['from_date'],
                'toDate' => $validated['to_date'],
            ]);
            return $pdf->download("{$filename}.pdf");
        }
    }
}
