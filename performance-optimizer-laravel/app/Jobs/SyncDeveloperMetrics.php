<?php

namespace App\Jobs;

use App\Services\CollectorService;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Support\Carbon;

class SyncDeveloperMetrics implements ShouldQueue
{
    use Queueable;

    /**
     * Create a new job instance.
     */
    public function __construct(
        public ?string $dateFrom = null,
        public ?string $dateTo = null,
        public ?int $developerId = null,
        public bool $syncGithub = true,
        public bool $syncWakatime = true,
        public bool $optimize = false
    ) {}

    /**
     * Execute the job.
     */
    public function handle(CollectorService $collectorService): void
    {
        $start = $this->dateFrom ? Carbon::parse($this->dateFrom) : now();
        $end = $this->dateTo ? Carbon::parse($this->dateTo) : $start->copy();

        for ($date = $start->copy(); $date->lte($end); $date->addDay()) {
            $collectorService->syncDailyMetrics(
                $date,
                $this->optimize,
                $this->developerId,
                $this->syncGithub,
                $this->syncWakatime
            );
        }
    }
}
