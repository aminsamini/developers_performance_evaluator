<?php

namespace App\Http\Controllers;

use App\Models\Repository;
use App\Services\GitHubService;
use Illuminate\Http\Request;

class RepositoryController extends Controller
{
    public function index()
    {
        return response()->json(Repository::all());
    }

    public function store(Request $request, GitHubService $gitHubService)
    {
        $validated = $request->validate([
            'name' => 'required|string|unique:repositories,name',
            'token' => 'nullable|string',
        ]);

        if (!empty($validated['token'])) {
            $isValid = $gitHubService->validateRepoToken($validated['name'], $validated['token']);
            if (!$isValid) {
                return response()->json(['detail' => 'Invalid GitHub Token or Repository not reachable.'], 400);
            }
        }

        $repository = Repository::create([
            'name' => $validated['name'],
            'token' => $validated['token'] ?? null,
            'status' => 'active',
        ]);

        return response()->json(['status' => 'created', 'name' => $repository->name]);
    }

    public function updateToken(Request $request, Repository $repository, GitHubService $gitHubService)
    {
        $validated = $request->validate([
            'token' => 'required|string',
        ]);

        $isValid = $gitHubService->validateRepoToken($repository->name, $validated['token']);
        if (!$isValid) {
            return response()->json(['detail' => 'Invalid Token or Repository not reachable'], 400);
        }

        $repository->update([
            'token' => $validated['token'],
            'status' => 'active',
            'last_error' => null,
            'last_checked' => now(),
        ]);

        return response()->json(['status' => 'success', 'message' => 'Token updated and verified']);
    }

    public function destroy(Repository $repository)
    {
        $repository->update(['status' => 'inactive']);
        return response()->json(['status' => 'deactivated', 'name' => $repository->name]);
    }

    public function activate(Repository $repository)
    {
        $repository->update(['status' => 'active']);
        return response()->json(['status' => 'activated', 'name' => $repository->name]);
    }
}
