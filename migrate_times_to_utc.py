import sqlite3
from datetime import datetime, timedelta
import pytz

# Configuration
DB_PATH = 'performance.db'
SOURCE_TZ = pytz.timezone('Asia/Tehran')
TARGET_TZ = pytz.UTC

def migrate_times():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch all metrics
    cursor.execute("SELECT id, date, start_work_time, end_work_time FROM metrics")
    rows = cursor.fetchall()

    print(f"Checking {len(rows)} records for migration...")
    updates_count = 0

    for row in rows:
        metric_id = row['id']
        date_str = row['date'] # YYYY-MM-DD
        start_str = row['start_work_time']
        end_str = row['end_work_time']

        new_start = start_str
        new_end = end_str
        changed = False

        if start_str and ':' in start_str:
            # Parse as Naive (implicitly Source TZ)
            # Strategy: Combine Date + Time -> Localize(Tehran) -> Convert(UTC) -> Extract Time
            try:
                dt_naive = datetime.strptime(f"{date_str} {start_str}", "%Y-%m-%d %H:%M")
                dt_local = SOURCE_TZ.localize(dt_naive)
                dt_utc = dt_local.astimezone(TARGET_TZ)
                new_start = dt_utc.strftime("%H:%M")
                if new_start != start_str:
                    changed = True
            except ValueError:
                pass # weird format, skip

        if end_str and ':' in end_str:
            try:
                dt_naive = datetime.strptime(f"{date_str} {end_str}", "%Y-%m-%d %H:%M")
                dt_local = SOURCE_TZ.localize(dt_naive)
                dt_utc = dt_local.astimezone(TARGET_TZ)
                new_end = dt_utc.strftime("%H:%M")
                if new_end != end_str:
                    changed = True
            except ValueError:
                pass

        if changed:
            cursor.execute(
                "UPDATE metrics SET start_work_time = ?, end_work_time = ? WHERE id = ?",
                (new_start, new_end, metric_id)
            )
            updates_count += 1
            print(f"Updated ID {metric_id}: {start_str}->{new_start}, {end_str}->{new_end}")

    conn.commit()
    conn.close()
    print(f"Migration complete. Updated {updates_count} records.")

if __name__ == "__main__":
    migrate_times()
