
import sqlite3
from backend.database import engine
from backend.models import Base, Metric

def reset_metrics():
    print("Resetting 'metrics' table due to schema corruption...")
    
    # 1. Drop existing table
    Metric.__table__.drop(engine)
    print("Dropped 'metrics' table.")
    
    # 2. Re-create table
    Base.metadata.create_all(bind=engine)
    print("Re-created 'metrics' table with correct schema.")

if __name__ == "__main__":
    reset_metrics()
