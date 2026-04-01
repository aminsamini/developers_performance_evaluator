<?php

namespace App\Exports;

use App\Models\Metric;
use Maatwebsite\Excel\Concerns\FromCollection;
use Maatwebsite\Excel\Concerns\WithHeadings;
use Maatwebsite\Excel\Concerns\WithMapping;

class MetricsExport implements FromCollection, WithHeadings, WithMapping
{
    public $metrics;

    public function __construct($metrics)
    {
        $this->metrics = $metrics;
    }

    /**
    * @return \Illuminate\Support\Collection
    */
    public function collection()
    {
        return $this->metrics;
    }

    public function headings(): array
    {
        return [
            'Developer',
            'Date',
            'Commits',
            'Lines Added',
            'Lines Deleted',
            'Files Modified',
            'Coding Time (mins)',
            'Score',
        ];
    }

    public function map($metric): array
    {
        return [
            $metric->developer?->name ?? 'Unknown',
            $metric->date instanceof \Carbon\Carbon ? $metric->date->toDateString() : ($metric->date ?? 'N/A'),
            $metric->commits_count ?? 0,
            $metric->lines_added ?? 0,
            $metric->lines_deleted ?? 0,
            $metric->files_modified ?? 0,
            floor(($metric->coding_time_seconds ?? 0) / 60),
            $metric->score ?? 0,
        ];
    }
}
