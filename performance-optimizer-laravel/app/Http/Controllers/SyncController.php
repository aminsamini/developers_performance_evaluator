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
        $results = $collectorService->syncHistoricalData(7, true);
        return response()->json(['status' => 'success', 'results' => $results]);
    }

    public function targetedSync(Request $request)
    {
        $validated = $request->validate([
            'developer_id' => 'nullable|integer',
            'date_from' => 'nullable|date_format:Y-m-d',
            'date_to' => 'nullable|date_format:Y-m-d',
            'sync_github' => 'boolean',
            'sync_wakatime' => 'boolean',
        ]);

        $dateFrom = $validated['date_from'] ?? now()->toDateString();
        $dateTo = $validated['date_to'] ?? now()->toDateString();

        SyncDeveloperMetrics::dispatch(
            $dateFrom,
            $dateTo,
            $validated['developer_id'] ?? null,
            $validated['sync_github'] ?? true,
            $validated['sync_wakatime'] ?? true,
            false // optimize
        );

        return response()->json(['status' => 'success', 'message' => 'Sync job dispatched']);
    }
}
