import os
import sys

# Add current path to sys.path to resolve imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal, Base
import models
from sqlalchemy import text

def clean_database():
    print("Creating all missing tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Cleaning data...")
        # 1. Delete dependent tables first
        db.query(models.Assessment).delete(synchronize_session=False)
        db.query(models.ObjectiveApproval).delete(synchronize_session=False)
        db.query(models.RubricApproval).delete(synchronize_session=False)
        db.query(models.RubricLevel).delete(synchronize_session=False)
        db.query(models.LearningObjective).delete(synchronize_session=False)
        db.query(models.TeacherRubric).delete(synchronize_session=False)
        
        # 2. Delete intermediate tables
        db.query(models.PlanningBimester).delete(synchronize_session=False)
        db.query(models.BnccLibrary).delete(synchronize_session=False)
        db.query(models.SpecificCompetency).delete(synchronize_session=False)
        db.query(models.TeacherClassDiscipline).delete(synchronize_session=False)
        db.query(models.Student).delete(synchronize_session=False)

        # 3. Delete base reference tables
        db.query(models.SetupClass).delete(synchronize_session=False)
        db.query(models.SetupDiscipline).delete(synchronize_session=False)
        
        # 4. Cleanup Users (keep only active)
        deleted_users = db.query(models.User).filter(models.User.is_active == False).delete(synchronize_session=False)
        
        db.commit()
        print(f"Database successfully cleaned! Inactive users deleted: {deleted_users}")
    except Exception as e:
        db.rollback()
        print(f"Error while cleaning: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clean_database()
