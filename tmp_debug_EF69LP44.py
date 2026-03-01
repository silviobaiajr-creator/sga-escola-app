from backend.database import SessionLocal
from backend.models import LearningObjective, SetupDiscipline

def test():
    db = SessionLocal()
    portugues = db.query(SetupDiscipline).filter(SetupDiscipline.discipline_name.ilike('%portugu%')).all()
    print("Disciplinas Portugues encontradas:")
    for d in portugues:
        print(f" -> {d.id} | {d.discipline_name}")
        
    objs = db.query(LearningObjective).filter(LearningObjective.bncc_code == 'EF69LP44').all()
    print("\nObjetivos da Habilidade EF69LP44:")
    for o in objs:
        print(f" -> Obj ID: {o.id} | Disc ID: {o.discipline_id} | Year: {o.year_level} | Bimester: {o.bimester} | Status: {o.status}")
        for r in o.rubric_levels:
            print(f"    - Rubric: {r.id} | Status: {r.status}")
        
    db.close()

if __name__ == "__main__":
    test()
