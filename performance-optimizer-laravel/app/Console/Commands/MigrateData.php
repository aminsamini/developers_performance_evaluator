<?php

namespace App\Console\Commands;

use App\Models\Developer;
use App\Models\Metric;
use App\Models\Repository;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;
use PDO;

class MigrateData extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'app:migrate-data {path}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Migrate data from old SQLite database';

    /**
     * Execute the console command.
     */
    public function handle()
    {
        $oldDbPath = $this->argument('path');

        if (!file_exists($oldDbPath)) {
            $this->error("Old database file not found at: {$oldDbPath}");
            return 1;
        }

        $this->info("Connecting to old database...");
        $oldPdo = new PDO("sqlite:{$oldDbPath}");
        $oldPdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        DB::beginTransaction();

        try {
            // 1. Migrate Developers
            $this->info("Migrating developers...");
            $oldDevelopers = $oldPdo->query("SELECT * FROM developers")->fetchAll(PDO::FETCH_ASSOC);
            foreach ($oldDevelopers as $dev) {
                Developer::updateOrCreate(
                    ['id' => $dev['id']],
                    [
                        'name' => $dev['name'],
                        'git_username' => $dev['git_username'],
                        'wakatime_api_key' => $dev['wakatime_api_key'],
                        'is_active' => (bool)$dev['is_active'],
                    ]
                );
            }

            // 2. Migrate Repositories
            $this->info("Migrating repositories...");
            $oldRepositories = $oldPdo->query("SELECT * FROM repositories")->fetchAll(PDO::FETCH_ASSOC);
            foreach ($oldRepositories as $repo) {
                Repository::updateOrCreate(
                    ['id' => $repo['id']],
                    [
                        'name' => $repo['name'],
                        'url' => $repo['url'] ?? null,
                        'token' => $repo['token'] ?? null,
                        'status' => $repo['status'] ?? 'active',
                        'last_error' => $repo['last_error'] ?? null,
                        'last_checked' => $repo['last_checked'] ?? null,
                    ]
                );
            }

            // 3. Migrate Metrics
            $this->info("Migrating metrics...");
            $oldMetrics = $oldPdo->query("SELECT * FROM metrics")->fetchAll(PDO::FETCH_ASSOC);
            foreach ($oldMetrics as $metric) {
                Metric::updateOrCreate(
                    ['id' => $metric['id']],
                    [
                        'developer_id' => $metric['developer_id'],
                        'date' => $metric['date'],
                        'commits_count' => $metric['commits_count'],
                        'lines_added' => $metric['lines_added'],
                        'lines_deleted' => $metric['lines_deleted'],
                        'files_modified' => $metric['files_modified'],
                        'churn_score' => $metric['churn_score'],
                        'coding_time_seconds' => $metric['coding_time_seconds'],
                        'active_coding_seconds' => $metric['active_coding_seconds'],
                        'deep_work_seconds' => $metric['deep_work_seconds'],
                        'start_work_time' => $metric['start_work_time'],
                        'end_work_time' => $metric['end_work_time'],
                        'project_focus_ratio' => $metric['project_focus_ratio'],
                        'context_switches' => $metric['context_switches'],
                        'wakatime_data' => $metric['wakatime_data'] ? json_decode($metric['wakatime_data'], true) : null,
                        'review_count' => $metric['review_count'] ?? 0,
                        'score' => $metric['score'],
                        'created_at' => $metric['updated_at'] ?? now(),
                        'updated_at' => $metric['updated_at'] ?? now(),
                    ]
                );
            }

            DB::commit();
            $this->info("Migration completed successfully!");
        } catch (\Exception $e) {
            DB::rollBack();
            $this->error("Migration failed: " . $e->getMessage());
            return 1;
        }

        return 0;
    }
}
