<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Exception;

class WakaTimeService
{
    protected string $baseUrl = 'https://wakatime.com/api/v1';

    public function fetchCodingTime(string $apiKey, string $day, ?array $allowedProjects = null): int
    {
        if (!$apiKey) {
            return 0;
        }

        $response = Http::get("{$this->baseUrl}/users/current/summaries", [
            'start' => $day,
            'end' => $day,
            'api_key' => $apiKey,
        ]);

        if (!$response->successful()) {
            throw new Exception("WakaTime API Summaries Error: {$response->status()}");
        }

        $data = $response->json();

        if (!empty($data['data'])) {
            $dayData = $data['data'][0];

            if ($allowedProjects) {
                $totalFilteredSeconds = 0;
                $projects = $dayData['projects'] ?? [];

                $normalize = function ($name) {
                    return strtolower(str_replace(['_', '-', ' '], '', $name));
                };

                $normalizedAllowed = array_map($normalize, $allowedProjects);

                foreach ($projects as $proj) {
                    $pName = $proj['name'];
                    $normName = $normalize($pName);

                    if (in_array($pName, $allowedProjects) || in_array($normName, $normalizedAllowed)) {
                        $totalFilteredSeconds += $proj['total_seconds'];
                    }
                }

                return (int)$totalFilteredSeconds;
            }

            return (int)($dayData['grand_total']['total_seconds'] ?? 0);
        }

        return 0;
    }

    public function fetchDurations(string $apiKey, string $day): array
    {
        if (!$apiKey) {
            return [];
        }

        $response = Http::get("{$this->baseUrl}/users/current/durations", [
            'date' => $day,
            'api_key' => $apiKey,
        ]);

        if ($response->status() === 402) {
            return [];
        }

        if (!$response->successful()) {
            return [];
        }

        $data = $response->json();
        return $data['data'] ?? [];
    }

    public function fetchDetailedSummary(string $apiKey, string $day): array
    {
        if (!$apiKey) {
            return [];
        }

        $response = Http::get("{$this->baseUrl}/users/current/summaries", [
            'start' => $day,
            'end' => $day,
            'api_key' => $apiKey,
        ]);

        if ($response->successful()) {
            $data = $response->json();
            return $data['data'][0] ?? [];
        }

        return [];
    }
}
