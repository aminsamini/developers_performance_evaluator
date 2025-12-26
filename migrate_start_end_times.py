import sqlite3
import os

DB_PATH = "performance.db"

def migrate_db():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(metrics)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "start_work_time" not in columns:
        print("Adding start_work_time column...")
        cursor.execute("ALTER TABLE metrics ADD COLUMN start_work_time VARCHAR")
    else:
        print("start_work_time column already exists.")

    if "end_work_time" not in columns:
        print("Adding end_work_time column...")
        cursor.execute("ALTER TABLE metrics ADD COLUMN end_work_time VARCHAR")
    else:
        print("end_work_time column already exists.")
        
    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate_db()
