import sqlite3

def add_wakatime_metrics_columns():
    db_path = "performance.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    columns = [
        ("active_coding_seconds", "INTEGER DEFAULT 0"),
        ("deep_work_seconds", "INTEGER DEFAULT 0"),
        ("project_focus_ratio", "FLOAT DEFAULT 0.0"),
        ("context_switches", "INTEGER DEFAULT 0"),
        ("wakatime_data", "TEXT")
    ]
    
    for col_name, col_type in columns:
        try:
            print(f"Attempting to add '{col_name}' column to 'metrics' table...")
            cursor.execute(f"ALTER TABLE metrics ADD COLUMN {col_name} {col_type}")
            print(f"Success: Column '{col_name}' added.")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"Notice: Column '{col_name}' already exists.")
            else:
                print(f"Error adding '{col_name}': {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_wakatime_metrics_columns()
