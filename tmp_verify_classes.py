from backend.database import SessionLocal
from backend.models import SetupClass

def test():
    db = SessionLocal()
    classes = db.query(SetupClass).all()
    for c in classes:
        print(f"Class: {c.class_name} | ID: {c.id} | Year Level: {c.year_level} | Shift: {c.shift}")
    db.close()

if __name__ == "__main__":
    test()
