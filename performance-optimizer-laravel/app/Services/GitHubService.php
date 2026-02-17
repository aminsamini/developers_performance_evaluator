<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Carbon;
use Exception;

class GitHubService
{
    protected string $baseUrl = 'https://api.github.com';

    public function fetchCommitsInRepo(string $username, string $repoName, string $sinceDate, ?string $untilDate = null, ?string $token = null): array
    {
        if (!$token) {
            return ['count' => 0, 'lines_added' => 0, 'lines_deleted' => 0, 'files_modified' => 0];
        }

        $since = Carbon::parse($sinceDate)->startOfDay();
        $until = $untilDate ? Carbon::parse($untilDate)->endOfDay() : $since->copy()->endOfDay();

        $response = Http::withToken($token)
            ->withHeaders(['Accept' => 'application/vnd.github.v3+json'])
            ->get("{$this->baseUrl}/repos/{$repoName}/commits", [
                'author' => $username,
                'since' => $since->toIso8601String(),
                'until' => $until->toIso8601String(),
                'per_page' => 100,
            ]);

        if ($response->status() === 401 || $response->status() === 403) {
            throw new Exception("GitHub Auth Error: {$response->status()}");
        }

        if (!$response->successful()) {
            throw new Exception("GitHub API Error: {$response->status()} {$response->body()}");
        }

        $commitsList = $response->json();
        $totalStats = [
            'count' => count($commitsList),
            'lines_added' => 0,
            'lines_deleted' => 0,
            'files_modified' => 0,
        ];

        foreach ($commitsList as $commit) {
            $sha = $commit['sha'];
            $detailResp = Http::withToken($token)
                ->withHeaders(['Accept' => 'application/vnd.github.v3+json'])
                ->get("{$this->baseUrl}/repos/{$repoName}/commits/{$sha}");

            if ($detailResp->successful()) {
                $detail = $detailResp->json();
                $stats = $detail['stats'] ?? ['additions' => 0, 'deletions' => 0];
                $files = $detail['files'] ?? [];

                $totalStats['lines_added'] += $stats['additions'];
                $totalStats['lines_deleted'] += $stats['deletions'];
                $totalStats['files_modified'] += count($files);
            }
        }

        return $totalStats;
    }

    public function validateRepoToken(string $repoName, string $token): bool
    {
        try {
            $response = Http::withToken($token)
                ->withHeaders(['Accept' => 'application/vnd.github.v3+json'])
                ->get("{$this->baseUrl}/repos/{$repoName}");

            return $response->successful();
        } catch (Exception $e) {
            return false;
        }
    }
}
