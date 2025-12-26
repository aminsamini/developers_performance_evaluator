import sqlite3

def list_repos():
    conn = sqlite3.connect('performance.db')
    cursor = conn.cursor()
    
    print("--- Searching for 'Laravel' in Repos ---")
    cursor.execute("SELECT name FROM repositories WHERE name LIKE '%Laravel%'")
    rows = cursor.fetchall()
    
    if not rows:
        print("No repositories found containing 'Laravel'.")
    else:
        for row in rows:
            print(f"- {row[0]}")

    conn.close()

if __name__ == "__main__":
    list_repos()
