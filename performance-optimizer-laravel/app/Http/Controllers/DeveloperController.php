<?php

namespace App\Http\Controllers;

use App\Models\Developer;
use Illuminate\Http\Request;
use Inertia\Inertia;

class DeveloperController extends Controller
{
    public function index()
    {
        return response()->json(Developer::all());
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'name' => 'required|string',
            'git_username' => 'required|string|unique:developers,git_username',
            'wakatime_api_key' => 'nullable|string',
        ]);

        $developer = Developer::create($validated);

        return response()->json(['status' => 'created', 'name' => $developer->name]);
    }

    public function update(Request $request, Developer $developer)
    {
        $validated = $request->validate([
            'name' => 'nullable|string',
            'git_username' => 'nullable|string|unique:developers,git_username,' . $developer->id,
            'wakatime_api_key' => 'nullable|string',
        ]);

        $developer->update(array_filter($validated));

        return response()->json(['status' => 'updated', 'developer' => $developer->name]);
    }

    public function destroy(Developer $developer)
    {
        $developer->update(['is_active' => false]);
        return response()->json(['status' => 'deactivated', 'developer' => $developer->name]);
    }

    public function activate(Developer $developer)
    {
        $developer->update(['is_active' => true]);
        return response()->json(['status' => 'activated', 'developer' => $developer->name]);
    }
}
