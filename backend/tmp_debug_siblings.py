from .database import SessionLocal
from .models import LearningObjective

def test():
    db = SessionLocal()
    objs = db.query(LearningObjective).filter(LearningObjective.status == "approved").all()

    print(f"Total de objetivos aprovados no banco: {len(objs)}")

    bncc_codes = list(set([o.bncc_code for o in objs]))
    print(f"BNCC codes desses objetivos: {bncc_codes}")
    
    for code in bncc_codes:
        all_objs = db.query(LearningObjective).filter(LearningObjective.bncc_code == code).all()
        print(f"\nPara a habilidade {code}, total de objs: {len(all_objs)}")
        for x in all_objs:
            print(f" -> Obj {x.id}: status={x.status}, bimester={x.bimester}")

    db.close()

if __name__ == "__main__":
    test()
