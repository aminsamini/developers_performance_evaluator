<?php

use App\Jobs\SyncDeveloperMetrics;
use Illuminate\Support\Facades\Schedule;

Schedule::job(new SyncDeveloperMetrics(optimize: true))->dailyAt('01:00');
