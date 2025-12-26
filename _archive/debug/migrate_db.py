from backend.database import SessionLocal, engine
from sqlalchemy import text

def add_token_column():
    print("Migrating database: Adding token column to repositories table...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE repositories ADD COLUMN token VARCHAR"))
            conn.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed (Column might already exist): {e}")

if __name__ == "__main__":
    add_token_column()
