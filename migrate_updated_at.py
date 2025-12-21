import sqlite3

def add_updated_at_column():
    db_path = "performance.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Attempting to add 'updated_at' column to 'metrics' table...")
        cursor.execute("ALTER TABLE metrics ADD COLUMN updated_at DATETIME")
        print("Success: Column 'updated_at' added.")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("Notice: Column 'updated_at' already exists.")
        else:
            print(f"Error: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_updated_at_column()
