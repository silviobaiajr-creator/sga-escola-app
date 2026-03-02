from backend.database import SessionLocal
from backend.models import LearningObjective, SetupClass, TeacherClassDiscipline, User
import json

def simulate_avaliacao_request(discipline_id, year_level, bimester):
    """Simula exatamente o que o backend faz ao receber a chamada do Menu Avaliação"""
    db = SessionLocal()
    
    q = db.query(LearningObjective).filter_by(
        discipline_id=discipline_id,
        year_level=year_level,
        bimester=bimester
    )
    rows = q.all()
    
    result = []
    for r in rows:
        has_rubrics = len(r.rubric_levels) > 0
        all_rubrics_approved = has_rubrics and all(rl.status == "approved" for rl in r.rubric_levels)
        rubrics_status = "approved" if all_rubrics_approved else ("pending" if has_rubrics else None)
        result.append({
            "id": str(r.id),
            "bncc_code": r.bncc_code,
            "bimester": r.bimester,
            "bimester_type": type(r.bimester).__name__,
            "status": r.status,
            "rubrics_status": rubrics_status,
            "has_rubrics": has_rubrics,
        })
    db.close()
    return result

def simulate_frontend_filter(allObjs, selectedBimester, fetchPastBimesters=False):
    """Simula exatamente o reducer do Frontend em Python"""
    skillStatusMap = {}
    skillsMap = {}
    
    for o in allObjs:
        code = o["bncc_code"] or "Sem BNCC"
        isApproved = o["status"] == "approved" and o["rubrics_status"] == "approved"
        
        if code not in skillStatusMap:
            skillStatusMap[code] = True
            skillsMap[code] = {
                "bncc_code": code,
                "bimester": int(o["bimester"]) if o["bimester"] is not None else 0
            }
        
        if not isApproved:
            skillStatusMap[code] = False
    
    validSkills = [sk for code, sk in skillsMap.items() if skillStatusMap.get(code) is True]
    
    if fetchPastBimesters:
        finalSkills = [sk for sk in validSkills if sk["bimester"] <= selectedBimester]
    else:
        finalSkills = [sk for sk in validSkills if sk["bimester"] == selectedBimester]
    
    return finalSkills, skillStatusMap, validSkills

def test():
    print("=" * 60)
    print("SIMULANDO REQUEST BACKEND para disco=1, year=7, bim=1")
    print("=" * 60)
    objs = simulate_avaliacao_request(discipline_id=1, year_level=7, bimester=1)
    print(f"Total de objetivos retornados: {len(objs)}")
    for o in objs:
        print(f"  BNCC: {o['bncc_code']} | Status: {o['status']} | Rubrics: {o['rubrics_status']}")
        print(f"  Bimester: {o['bimester']} (type={o['bimester_type']})")

    print("\n" + "=" * 60)
    print("SIMULANDO REDUCER FRONTEND (bimester=1, fetchPastBimesters=False)")
    print("=" * 60)
    finalSkills, skillStatusMap, validSkills = simulate_frontend_filter(objs, 1, False)
    print(f"skillStatusMap: {skillStatusMap}")
    print(f"validSkills: {validSkills}")
    print(f"finalSkills (filtrado por bimester=1): {finalSkills}")
    
    print("\n" + "=" * 60)
    print("SIMULANDO REQUEST SEM BIMESTER (fetchPastBimesters=True)")
    print("=" * 60)
    # Quando fetchPastBimesters=True, bimester=undefined -> bimester is NOT passed
    # Na API Python, bimester é obrigatório! Então retorna 422 e o catch silencia
    # Vamos verificar o que acontece se a query omite bimester
    db = SessionLocal()
    try:
        q = db.query(LearningObjective).filter_by(discipline_id=1, year_level=7)
        rows_no_bim = q.all()
        print(f"Sem filtro bimester: {len(rows_no_bim)} objetivos")
        for r in rows_no_bim:
            print(f"  Bimester={r.bimester} (type={type(r.bimester).__name__})")
    finally:
        db.close()

if __name__ == "__main__":
    test()
