<?php

namespace App\Http\Controllers;

use App\Jobs\SyncDeveloperMetrics;
use App\Services\CollectorService;
use Illuminate\Http\Request;
use Illuminate\Support\Carbon;

class SyncController extends Controller
{
    public function sync(CollectorService $collectorService)
    {
        set_time_limit(600); // Allow up to 10 minutes for 7-day sync
        $results = $collectorService->syncHistoricalData(7, true);
        return response()->json(['status' => 'success', 'results' => $results]);
    }

    public function targetedSync(Request $request, CollectorService $collectorService)
    {
        set_time_limit(300); // Allow up to 5 minutes for sync
        $validated = $request->validate([
            'developer_id' => 'nullable|integer',
            'date_from' => 'nullable|date_format:Y-m-d',
            'date_to' => 'nullable|date_format:Y-m-d',
            'sync_github' => 'boolean',
            'sync_wakatime' => 'boolean',
        ]);

        $dateFrom = $validated['date_from'] ?? now()->toDateString();
        $dateTo = $validated['date_to'] ?? now()->toDateString();

        $start = Carbon::parse($dateFrom);
        $end = Carbon::parse($dateTo);
        $allResults = [];

        for ($date = $start->copy(); $date->lte($end); $date->addDay()) {
            $dayResults = $collectorService->syncDailyMetrics(
                $date->copy(),
                false, // optimize
                $validated['developer_id'] ?? null,
                $validated['sync_github'] ?? true,
                $validated['sync_wakatime'] ?? true
            );
            $allResults = array_merge($allResults, $dayResults);
        }

        return response()->json([
            'status' => 'success',
            'message' => 'Sync completed',
            'results' => $allResults,
        ]);
    }
}
