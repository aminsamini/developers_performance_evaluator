import sys
import os

# Add project root to path to allow importing backend modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.database import SessionLocal
from backend.models import Metric
from backend.services.score_calculator import calculate_developer_score

def recalculate():
    print("Starting score recalculation...")
    db = SessionLocal()
    try:
        metrics = db.query(Metric).all()
        print(f"Found {len(metrics)} metrics to recalculate.")
        
        updated_count = 0
        for m in metrics:
            old_score = m.score
            new_score = calculate_developer_score(
                commits=m.commits_count or 0,
                files_modified=m.files_modified or 0,
                lines_added=m.lines_added or 0,
                lines_deleted=m.lines_deleted or 0,
                churn_score=m.churn_score or 0.0,
                active_coding_seconds=m.active_coding_seconds or 0,
                deep_work_seconds=m.deep_work_seconds or 0,
                project_focus_ratio=m.project_focus_ratio or 0.0,
                context_switches=m.context_switches or 0
            )
            m.score = new_score
            updated_count += 1
        
        db.commit()
        print(f"Successfully recalculated and updated {updated_count} metric scores.")
        
    except Exception as e:
        print(f"Error during recalculation: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    recalculate()
