
import sqlite3

def inspect():
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()
    
    # Get all columns
    cursor.execute("PRAGMA table_info(metrics)")
    columns = cursor.fetchall()
    col_names = [c[1] for c in columns]
    print(f"Columns: {col_names}")
    
    cursor.execute("SELECT * FROM metrics WHERE id = 1")
    row = cursor.fetchone()
    
    if row:
        print("\nRow Data:")
        for name, value in zip(col_names, row):
            print(f"{name}: {value}")
    else:
        print("Metric ID 1 not found")

if __name__ == "__main__":
    inspect()
