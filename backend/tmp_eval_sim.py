from .database import SessionLocal
from .models import LearningObjective

def test():
    db = SessionLocal()
    # Puxar objectives igual 'avaliacao/page.tsx' getObjectives faz:
    # discipline_id=1, year_level=6, bimester=1
    objs = db.query(LearningObjective).filter(
        LearningObjective.discipline_id == 1,
        LearningObjective.year_level == 6
    ).all()
    
    print(f"Total objetivos BD para D1 Y6: {len(objs)}")
    
    # Replica logic
    skillStatusMap = {}
    skillsMap = {}
    
    for r in objs:
        print(f"\nObj ID {r.id}: {r.bncc_code} | Bim: {r.bimester} | Status: {r.status}")
        
        has_rubrics = len(r.rubric_levels) > 0
        all_rubrics_approved = has_rubrics and all(rl.status == "approved" for rl in r.rubric_levels)
        rubrics_status = "approved" if all_rubrics_approved else ("pending" if has_rubrics else None)
        
        print(f" -> has_rubrics={has_rubrics}, rubrics_status={rubrics_status}")
        
        code = r.bncc_code or "Sem BNCC"
        isApproved = (r.status == "approved") and (rubrics_status == "approved")
        
        if code not in skillStatusMap:
            skillStatusMap[code] = True
            skillsMap[code] = {
                "bncc_code": code,
                "bimester": r.bimester
            }
            
        if not isApproved:
            skillStatusMap[code] = False
            
    print("\n--- Final Map ---")
    print(skillStatusMap)
    
    validSkills = [sk for code, sk in skillsMap.items() if skillStatusMap.get(code) is True]
    print(f"Valid Skills: {validSkills}")
    
    finalSkills = [sk for sk in validSkills if sk["bimester"] == 1]
    print(f"Final Skills (bimester=1): {finalSkills}")
    
if __name__ == "__main__":
    test()
