from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.abspath("backend"))
from backend.main import app

client = TestClient(app)

def test():
    # Login as admin or test getting classes directly
    # To bypass auth for this debug, we'll just check if it fails 422
    # Oh wait, we need 'all=true' on an authenticated request to get all classes..
    from backend.database import SessionLocal
    from backend.models import SetupClass
    from backend.routers.admin import list_classes
    
    db = SessionLocal()
    # Mocking list_classes without current_user filter
    classes = db.query(SetupClass).all()
    out = [
        {
            "id": r.id, 
            "class_name": r.class_name,
            "year_level": r.year_level, 
            "school_year": r.school_year,
            "shift": r.shift
        }
        for r in classes
    ]
    print(out)

if __name__ == "__main__":
    test()
