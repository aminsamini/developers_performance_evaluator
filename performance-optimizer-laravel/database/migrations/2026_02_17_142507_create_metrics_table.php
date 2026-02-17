<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('metrics', function (Blueprint $t) {
            $t->id();
            $t->foreignId('developer_id')->constrained()->onDelete('cascade');
            $t->date('date')->index();

            // Git Metrics
            $t->integer('commits_count')->default(0);
            $t->integer('lines_added')->default(0);
            $t->integer('lines_deleted')->default(0);
            $t->integer('files_modified')->default(0);
            $t->float('churn_score')->default(0.0);

            // WakaTime Metrics
            $t->integer('coding_time_seconds')->default(0);
            $t->integer('active_coding_seconds')->default(0);
            $t->integer('deep_work_seconds')->default(0);
            $t->timestamp('start_work_time')->nullable();
            $t->timestamp('end_work_time')->nullable();
            $t->float('project_focus_ratio')->default(0.0);
            $t->integer('context_switches')->default(0);
            $t->json('wakatime_data')->nullable();

            // Review Metrics
            $t->integer('review_count')->default(0);

            // Score
            $t->float('score')->default(0.0);

            $t->timestamps();

            $t->unique(['developer_id', 'date']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('metrics');
    }
};
