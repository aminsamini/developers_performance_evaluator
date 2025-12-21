import asyncio
import datetime
from backend.services import collector
from backend.database import SessionLocal
from backend.models import Developer

async def force_resync_last_10_days():
    db = SessionLocal()
    developers = db.query(Developer).all()
    
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=10)
    
    print(f"--- Focing Re-Sync from {start_date} to {today} ---")
    
    # We loop each day
    current = start_date
    while current <= today:
        print(f"\nSyncing Date: {current}")
        # We call sync_daily_metrics with optimize=False to FORCE update
        try:
           await collector.sync_daily_metrics(db, current, optimize=False)
        except Exception as e:
           print(f"Error syncing {current}: {e}")
        
        current += datetime.timedelta(days=1)
    
    db.close()
    print("\n--- Force Re-Sync Completed ---")

if __name__ == "__main__":
    asyncio.run(force_resync_last_10_days())
