<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Metric extends Model
{
    use HasFactory;

    protected $fillable = [
        'developer_id',
        'date',
        'commits_count',
        'lines_added',
        'lines_deleted',
        'files_modified',
        'churn_score',
        'coding_time_seconds',
        'active_coding_seconds',
        'deep_work_seconds',
        'start_work_time',
        'end_work_time',
        'project_focus_ratio',
        'context_switches',
        'wakatime_data',
        'review_count',
        'score',
    ];

    protected $casts = [
        'date' => 'date',
        'start_work_time' => 'datetime',
        'end_work_time' => 'datetime',
        'wakatime_data' => 'array',
        'churn_score' => 'float',
        'project_focus_ratio' => 'float',
        'score' => 'float',
    ];

    public function developer(): BelongsTo
    {
        return $this->belongsTo(Developer::class);
    }
}
