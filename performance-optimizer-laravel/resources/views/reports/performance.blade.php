<!DOCTYPE html>
<html>
<head>
    <title>Performance Report</title>
    <style>
        body { font-family: sans-serif; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        h1 { text-align: center; }
        .summary { margin-bottom: 20px; }
    </style>
</head>
<body>
    <h1>Performance Report</h1>
    <div class="summary">
        <p><strong>Period:</strong> {{ $fromDate }} to {{ $toDate }}</p>
        <p><strong>Generated at:</strong> {{ now() }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Developer</th>
                <th>Date</th>
                <th>Commits</th>
                <th>Lines +</th>
                <th>Lines -</th>
                <th>Time (mins)</th>
                <th>Score</th>
            </tr>
        </thead>
        <tbody>
            @foreach($metrics as $metric)
            <tr>
                <td>{{ $metric->developer->name }}</td>
                <td>{{ $metric->date->toDateString() }}</td>
                <td>{{ $metric->commits_count }}</td>
                <td>{{ $metric->lines_added }}</td>
                <td>{{ $metric->lines_deleted }}</td>
                <td>{{ floor($metric->coding_time_seconds / 60) }}</td>
                <td>{{ $metric->score }}</td>
            </tr>
            @endforeach
        </tbody>
    </table>
</body>
</html>
