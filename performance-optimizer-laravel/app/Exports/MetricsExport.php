<?php

namespace App\Exports;

use App\Models\Metric;
use Maatwebsite\Excel\Concerns\FromCollection;
use Maatwebsite\Excel\Concerns\WithHeadings;
use Maatwebsite\Excel\Concerns\WithMapping;

class MetricsExport implements FromCollection, WithHeadings, WithMapping
{
    public function __construct(protected $metrics)
    {
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
            $metric->developer->name,
            $metric->date->toDateString(),
            $metric->commits_count,
            $metric->lines_added,
            $metric->lines_deleted,
            $metric->files_modified,
            floor($metric->coding_time_seconds / 60),
            $metric->score,
        ];
    }
}
