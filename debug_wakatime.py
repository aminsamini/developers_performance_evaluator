import asyncio
import os
import httpx
from datetime import date, timedelta
from backend.database import SessionLocal
from backend.models import Developer

async def debug_wakatime():
    db = SessionLocal()
    developers = db.query(Developer).all()
    
    if not developers:
        print("No developers found.")
        return

    async with httpx.AsyncClient() as client:
        for dev in developers:
            if not dev.wakatime_api_key:
                print(f"Skipping {dev.name} (No API Key)")
                continue
                
            print(f"\n--- Debugging WakaTime for {dev.name} ---")
            today = date.today()
            
            # Check last 3 days
            for i in range(3):
                target_date = today - timedelta(days=i)
                print(f"  Date: {target_date}")
                
                try:
                    # Raw API Call to see what projects exist
                    response = await client.get(
                        "https://wakatime.com/api/v1/users/current/summaries",
                        params={
                            "start": target_date.isoformat(),
                            "end": target_date.isoformat(),
                            "api_key": dev.wakatime_api_key
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("data"):
                            day_data = data["data"][0]
                            grand_total = day_data["grand_total"]["text"]
                            projects = day_data.get("projects", [])
                            
                            print(f"    Grand Total: {grand_total}")
                            print(f"    Projects found ({len(projects)}):")
                            for p in projects:
                                print(f"      - Name: '{p['name']}' | Time: {p['text']} ({p['total_seconds']}s)")
                        else:
                            print("    No data returned.")
                    else:
                        print(f"    API Error: {response.status_code}")
                        
                except Exception as e:
                    print(f"    Error: {e}")

    db.close()

if __name__ == "__main__":
    asyncio.run(debug_wakatime())
