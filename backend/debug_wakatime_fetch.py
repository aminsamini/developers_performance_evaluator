import asyncio
import os
from datetime import date
from backend import database, models
from backend.services.wakatime_service import WakaTimeService

async def debug_fetch():
    db = database.SessionLocal()
    
    # Get Developer
    dev_name = "Mohammad Badri"
    dev = db.query(models.Developer).filter(models.Developer.name == dev_name).first()
    
    if not dev:
        print(f"Developer {dev_name} not found!")
        return

    print(f"--- Debugging WakaTime for {dev.name} ---")
    print(f"API Key: {dev.wakatime_api_key[:5]}... (Masked)")
    
    target_date = date(2025, 12, 24)
    print(f"Target Date: {target_date}")
    
    service = WakaTimeService()
    
    # 1. Fetch Coding Time (Grand Total)
    print("\nFetching Coding Time (Grand Total)...")
    seconds = await service.fetch_coding_time(dev.wakatime_api_key, target_date)
    print(f"  Result Seconds: {seconds}")
    print(f"  Result Minutes: {seconds / 60}")
    print(f"  Result Hours:   {seconds / 3600}")

    # 2. Fetch Detailed Summary (to see breakdown)
    print("\nFetching Detailed Summary...")
    summary = await service.fetch_detailed_summary(dev.wakatime_api_key, target_date)
    
    if summary:
        print(f"  Grand Total Text: {summary.get('grand_total', {}).get('text')}")
        print(f"  Grand Total Secs: {summary.get('grand_total', {}).get('total_seconds')}")
        print("  Projects:")
        for p in summary.get('projects', []):
            print(f"    - {p['name']}: {p['text']} ({p['total_seconds']}s)")
    else:
        print("  No summary returned.")

    # 3. Fetch Durations (to compare vs Summary)
    print("\nFetching Durations...")
    durations = await service.fetch_durations(dev.wakatime_api_key, target_date)
    duration_sum = sum(d.get('duration', 0) for d in durations)
    print(f"  Durations Sum: {duration_sum} seconds")
    print(f"  Durations Mins: {duration_sum / 60}")
    print(f"  Durations Hours: {duration_sum / 3600}")
    
    # 4. Filter Durations by Project (Simulate old logic?)
    # ...

    db.close()

if __name__ == "__main__":
    asyncio.run(debug_fetch())
