import sqlite3
from dateutil import parser

DB_PATH = 'performance.db'

def fix_inverted_times():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, start_work_time, end_work_time FROM metrics WHERE start_work_time IS NOT NULL AND end_work_time IS NOT NULL")
    rows = cursor.fetchall()

    print(f"Checking {len(rows)} records for inversion...")
    fixed = 0

    for row in rows:
        metric_id = row['id']
        start_str = row['start_work_time']
        end_str = row['end_work_time']
        
        try:
            # Parse ISO strings
            s = parser.parse(start_str)
            e = parser.parse(end_str)
            
            if s > e:
                print(f"Fixing ID {metric_id}: Start {start_str} > End {end_str}")
                # Swap
                cursor.execute(
                    "UPDATE metrics SET start_work_time = ?, end_work_time = ? WHERE id = ?",
                    (end_str, start_str, metric_id)
                )
                fixed += 1
        except Exception as err:
            print(f"Skipping ID {metric_id}: Parse error {err}")

    conn.commit()
    conn.close()
    print(f"Fixed {fixed} records.")

if __name__ == "__main__":
    fix_inverted_times()
