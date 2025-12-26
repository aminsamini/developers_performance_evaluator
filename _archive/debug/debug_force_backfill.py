import asyncio
from datetime import date
from backend.database import SessionLocal
from backend.services import collector
from backend.models import Metric, Developer

async def force_backfill():
    # Last known commit was 2025-10-24
    target_date = date(2025, 10, 24)
    print(f"--- Forcing Sync for {target_date} ---")
    
    db = SessionLocal()
    
    # Run the existing sync logic
    await collector.sync_daily_metrics(db, target_date)
    
    # Check results
    print("\nChecking Metrics in DB for that date:")
    metrics = db.query(Metric).filter(Metric.date == target_date).all()
    for m in metrics:
        dev = db.query(Developer).get(m.developer_id)
        print(f"  - {dev.name}: {m.commits_count} commits")
        
    db.close()

if __name__ == "__main__":
    asyncio.run(force_backfill())
