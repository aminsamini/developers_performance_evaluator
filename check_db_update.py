import sqlite3

def check_db():
    try:
        conn = sqlite3.connect('performance.db')
        cursor = conn.cursor()
        
        print("--- Checking Metrics for 2025-12-15 (Dev ID 3) ---")
        cursor.execute("SELECT id, developer_id, date, coding_time_seconds, score, active_coding_seconds FROM metrics WHERE date = '2025-12-15' AND developer_id = 3")
        rows = cursor.fetchall()
                
        if not rows:
            print("No records found for 2025-12-15 (Dev 3) yet.")
        
        for row in rows:
            print(f"ID: {row[0]} | Dev: {row[1]} | Date: {row[2]} | Coding Time: {row[3]} | Active: {row[5]}")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
