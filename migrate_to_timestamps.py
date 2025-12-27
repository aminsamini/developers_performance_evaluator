import sqlite3
from datetime import datetime, timedelta
import pytz

# Configuration
DB_PATH = 'performance.db'
TEHRAN_TZ = pytz.timezone('Asia/Tehran')
UTC_TZ = pytz.UTC

def migrate_to_timestamps():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch all metrics
    cursor.execute("SELECT id, date, start_work_time, end_work_time FROM metrics")
    rows = cursor.fetchall()

    print(f"Checking {len(rows)} records for timestamp migration...")
    updates_count = 0

    for row in rows:
        metric_id = row['id']
        date_str = row['date'] # YYYY-MM-DD
        start_str = row['start_work_time'] # UTC "HH:MM" or None
        end_str = row['end_work_time']     # UTC "HH:MM" or None

        new_start = None
        new_end = None
        changed = False

        if start_str and ':' in start_str and 'T' not in start_str:
             # Find correct timestamp
             new_start = resolve_timestamp(date_str, start_str)
             if new_start != start_str:
                 changed = True
        
        if end_str and ':' in end_str and 'T' not in end_str:
             new_end = resolve_timestamp(date_str, end_str)
             if new_end != end_str:
                 changed = True

        if changed:
            # Update
            # We keep new_start as None if resolution failed (shouldn't happen if valid)
            # If original was valid string, new must be ISO string
            s_val = new_start if new_start else start_str
            e_val = new_end if new_end else end_str
            
            cursor.execute(
                "UPDATE metrics SET start_work_time = ?, end_work_time = ? WHERE id = ?",
                (s_val, e_val, metric_id)
            )
            updates_count += 1
            print(f"Updated ID {metric_id}: {start_str} -> {s_val}")

    conn.commit()
    conn.close()
    print(f"Migration complete. Updated {updates_count} records.")

def resolve_timestamp(reported_date_str, utc_time_str):
    """
    Finds the UTC timestamp that, when converted to Tehran time, 
    falls on reported_date_str.
    utc_time_str is "HH:MM" (UTC).
    """
    try:
        report_date = datetime.strptime(reported_date_str, "%Y-%m-%d").date()
        h, m = map(int, utc_time_str.split(':'))
        
        # Candidates: report_date, prev_day, next_day
        # We construct UTC datetime for each candidate day + utc_time
        # Convert to Tehran
        # Check if Tehran Date == report_date
        
        candidates = [0, -1, 1]
        for offset in candidates:
            candidate_date = report_date + timedelta(days=offset)
            # Construct UTC naive then localized
            dt_utc = datetime(candidate_date.year, candidate_date.month, candidate_date.day, h, m)
            dt_utc_aware = UTC_TZ.localize(dt_utc)
            
            # Convert to Tehran
            dt_tehran = dt_utc_aware.astimezone(TEHRAN_TZ)
            
            if dt_tehran.date() == report_date:
                # Found match! Return ISO format
                return dt_utc_aware.isoformat()
        
        # If no match logic found (should be rare), fallback to report_date
        # This simplifies "just assume it was that day"
        print(f"WARN: Could not match date for {reported_date_str} {utc_time_str}")
        dt_fallback = datetime(report_date.year, report_date.month, report_date.day, h, m)
        return UTC_TZ.localize(dt_fallback).isoformat()

    except Exception as e:
        print(f"Error converting {reported_date_str} {utc_time_str}: {e}")
        return utc_time_str

if __name__ == "__main__":
    migrate_to_timestamps()
