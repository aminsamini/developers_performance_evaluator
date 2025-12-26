from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import database, models

def deduplicate():
    db = database.SessionLocal()
    print("--- Starting Deduplication ---")
    
    # 1. Identify duplicates
    # Group by developer_id and date
    duplicates = db.query(
        models.Metric.developer_id, 
        models.Metric.date, 
        func.count(models.Metric.id)
    ).group_by(
        models.Metric.developer_id, 
        models.Metric.date
    ).having(
        func.count(models.Metric.id) > 1
    ).all()
    
    print(f"Found {len(duplicates)} days with duplicate records.")
    
    for dev_id, day, count in duplicates:
        print(f"  Dev {dev_id} on {day}: {count} records. Keeping latest.")
        
        # Fetch all records for this dup set
        records = db.query(models.Metric).filter(
            models.Metric.developer_id == dev_id,
            models.Metric.date == day
        ).order_by(models.Metric.id.desc()).all()
        
        # Keep the first one (latest ID), delete the rest
        # Or should we keep the one with the highest score? 
        # For now, latest ID is likely the most recent sync.
        keep = records[0]
        remove = records[1:]
        
        for r in remove:
            db.delete(r)
            
    db.commit()
    print("Deduplication complete.")
    db.close()

if __name__ == "__main__":
    deduplicate()
