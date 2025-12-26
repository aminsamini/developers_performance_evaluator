from backend import database, models
from sqlalchemy import text

def inspect():
    db = database.SessionLocal()
    print("--- Inspecting Metrics for 2025-12-24 ---")
    
    # Raw SQL to see exactly what is stored
    result = db.execute(text("SELECT id, developer_id, date, score FROM metrics WHERE date = '2025-12-24'"))
    rows = result.fetchall()
    print(f"Total Rows for 2025-12-24: {len(rows)}")
    for r in rows:
        print(r)
        
    db.close()

if __name__ == "__main__":
    inspect()
