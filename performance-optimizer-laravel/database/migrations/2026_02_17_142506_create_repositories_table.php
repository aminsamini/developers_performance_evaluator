<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('repositories', function (Blueprint $t) {
            $t->id();
            $t->string('name')->unique()->index();
            $t->string('url')->nullable();
            $t->string('token')->nullable();
            $t->string('status')->default('active');
            $t->text('last_error')->nullable();
            $t->timestamp('last_checked')->nullable();
            $t->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('repositories');
    }
};
