<?php

use App\Http\Controllers\DeveloperController;
use App\Http\Controllers\MetricController;
use App\Http\Controllers\ReportController;
use App\Http\Controllers\RepositoryController;
use App\Http\Controllers\SyncController;
use Illuminate\Support\Facades\Route;

Route::prefix('developers')->group(function () {
    Route::get('/', [DeveloperController::class, 'index']);
    Route::post('/', [DeveloperController::class, 'store']);
    Route::put('/{developer}', [DeveloperController::class, 'update']);
    Route::delete('/{developer}', [DeveloperController::class, 'destroy']);
    Route::post('/{developer}/activate', [DeveloperController::class, 'activate']);
});

Route::prefix('repositories')->group(function () {
    Route::get('/', [RepositoryController::class, 'index']);
    Route::post('/', [RepositoryController::class, 'store']);
    Route::delete('/{repository}', [RepositoryController::class, 'destroy']);
    Route::post('/{repository}/activate', [RepositoryController::class, 'activate']);
    Route::put('/{repository}/token', [RepositoryController::class, 'updateToken']);
});

Route::prefix('metrics')->group(function () {
    Route::get('/', [MetricController::class, 'index']);
    Route::get('/summary', [MetricController::class, 'summary']);
    Route::get('/detail/{developerId}/{dateStr}', [MetricController::class, 'show']);
});

Route::post('/sync', [SyncController::class, 'sync']);
Route::post('/sync/target', [SyncController::class, 'targetedSync']);

Route::prefix('reports')->group(function () {
    Route::post('/generate', [ReportController::class, 'generate']);
});

Route::post('/export/report', [ReportController::class, 'export']);
