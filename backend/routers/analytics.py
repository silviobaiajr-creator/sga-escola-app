"""
Router de Analytics — Dashboard rico do coordenador e evolução por aluno.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from ..database import get_db
from .. import models

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard")
def get_dashboard(
    discipline_id: Optional[int] = None,
    year_level: Optional[int] = None,
    bimester: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Dados ricos para o dashboard do coordenador pedagógico.
    Retorna: distribuição de níveis por turma, médias, alunos em risco.
    """
    from datetime import datetime
    school_year = datetime.now().year

    # --- Query base de avaliações ---
    q = db.query(
        models.Assessment.class_name,
        models.Assessment.level_assigned,
        models.Assessment.bncc_code,
        models.Assessment.discipline_id,
        models.Assessment.bimester,
        func.count(models.Assessment.id).label("count")
    ).filter(models.Assessment.level_assigned != None)

    if discipline_id:
        q = q.filter(models.Assessment.discipline_id == discipline_id)
    if bimester:
        q = q.filter(models.Assessment.bimester == bimester)

    rows = q.group_by(
        models.Assessment.class_name,
        models.Assessment.level_assigned,
        models.Assessment.bncc_code,
        models.Assessment.discipline_id,
        models.Assessment.bimester
    ).all()

    # --- Distribuição geral de níveis (para gráfico de barras) ---
    level_dist = {1: 0, 2: 0, 3: 0, 4: 0}
    class_summary = {}
    skill_summary = {}

    for row in rows:
        level = row.level_assigned
        count = row.count
        class_name = row.class_name or "Sem turma"
        bncc = row.bncc_code

        # Distribuição global
        if level in level_dist:
            level_dist[level] += count

        # Por turma
        if class_name not in class_summary:
            class_summary[class_name] = {1: 0, 2: 0, 3: 0, 4: 0, "total": 0}
        if level in class_summary[class_name]:
            class_summary[class_name][level] += count
        class_summary[class_name]["total"] += count

        # Por habilidade
        if bncc not in skill_summary:
            skill_summary[bncc] = {"total": 0, "sum_levels": 0, "levels": {1:0,2:0,3:0,4:0}}
        skill_summary[bncc]["total"] += count
        skill_summary[bncc]["sum_levels"] += level * count
        if level in skill_summary[bncc]["levels"]:
            skill_summary[bncc]["levels"][level] += count

    # Calcular médias por turma
    class_averages = []
    for cn, data in class_summary.items():
        total = data["total"]
        if total > 0:
            weighted_sum = sum(lv * data[lv] for lv in [1, 2, 3, 4])
            avg = round(weighted_sum / total, 2)
        else:
            avg = 0
        at_risk = data[1] + data[2]  # N1 + N2
        class_averages.append({
            "class_name": cn,
            "average_level": avg,
            "level_distribution": {str(k): data[k] for k in [1, 2, 3, 4]},
            "total_assessments": total,
            "at_risk_count": at_risk,
            "at_risk_pct": round(at_risk / total * 100, 1) if total > 0 else 0
        })
    class_averages.sort(key=lambda x: x["class_name"])

    # Top habilidades com baixo desempenho
    skill_alerts = []
    for code, data in skill_summary.items():
        if data["total"] > 0:
            avg = round(data["sum_levels"] / data["total"], 2)
            at_risk_pct = round((data["levels"][1] + data["levels"][2]) / data["total"] * 100, 1)
            skill_alerts.append({
                "bncc_code": code, "average_level": avg, "at_risk_pct": at_risk_pct,
                "total": data["total"]
            })
    skill_alerts.sort(key=lambda x: x["average_level"])

    # --- Contagem geral ---
    total_students = db.query(models.Student).filter_by(status="active").count()
    total_assessments = db.query(models.Assessment).count()
    approved_objectives = db.query(models.LearningObjective).filter_by(status="approved").count()
    pending_approvals = db.query(models.LearningObjective).filter_by(status="pending").count()

    return {
        "level_distribution": level_dist,          # Para gráfico de pizza/barras
        "class_averages": class_averages,           # Para tabela/gráfico de turmas
        "skill_alerts": skill_alerts[:10],          # Top 10 habilidades com baixo desempenho
        "summary": {
            "total_students": total_students,
            "total_assessments": total_assessments,
            "approved_objectives": approved_objectives,
            "pending_approvals": pending_approvals
        }
    }


@router.get("/evolution/{student_id}")
def get_student_evolution(
    student_id: str,
    discipline_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Evolução de um aluno: notas por habilidade (média dos objetivos) e por objetivo."""
    q = db.query(models.Assessment).filter_by(student_id=student_id)
    if discipline_id:
        q = q.filter_by(discipline_id=discipline_id)
    assessments = q.order_by(models.Assessment.date).all()

    # Agrupar por habilidade BNCC
    by_skill: dict = {}
    for a in assessments:
        code = a.bncc_code
        if code not in by_skill:
            by_skill[code] = {"levels": [], "bimester": a.bimester, "objectives": {}}
            
        if a.level_assigned:
            by_skill[code]["levels"].append(a.level_assigned)
            
            obj_id = str(a.objective_id) if a.objective_id else "general"
            if obj_id not in by_skill[code]["objectives"]:
                by_skill[code]["objectives"][obj_id] = {"levels": [], "description": a.objective.description if a.objective else "Avaliação Geral"}
            by_skill[code]["objectives"][obj_id]["levels"].append(a.level_assigned)

    skill_evolution = []
    for code, data in by_skill.items():
        skill = db.query(models.BnccLibrary).get(code)
        
        levels = [l for l in data["levels"] if l is not None]
        avg = round(sum(levels) / len(levels), 2) if levels else 0
        
        obj_list = []
        for obj_id, obj_data in data["objectives"].items():
            obj_levels = obj_data["levels"]
            obj_avg = round(sum(obj_levels) / len(obj_levels), 2) if obj_levels else 0
            obj_list.append({
                "objective_id": obj_id,
                "description": obj_data["description"],
                "average_level": obj_avg,
                "assessments": len(obj_levels)
            })
            
        skill_evolution.append({
            "bncc_code": code,
            "skill_description": skill.skill_description if skill else "Habilidade não encontrada",
            "average_level": avg,
            "assessments": len(levels),
            "bimester": data["bimester"],
            "objectives": obj_list
        })
    skill_evolution.sort(key=lambda x: x["bimester"] or 0)

    # Student info
    student = db.query(models.Student).get(student_id)

    return {
        "student_id": student_id,
        "student_name": student.student_name if student else student_id,
        "class_name": student.class_name if student else None,
        "skill_evolution": skill_evolution,
        "total_assessments": len(assessments)
    }


@router.get("/class-radar/{class_name}")
def get_class_radar(
    class_name: str,
    discipline_id: Optional[int] = None,
    bimester: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Dados para gráfico radar de competências de uma turma."""
    q = db.query(models.Assessment).filter_by(class_name=class_name)
    if discipline_id:
        q = q.filter_by(discipline_id=discipline_id)
    if bimester:
        q = q.filter_by(bimester=bimester)
    assessments = q.all()

    by_skill: dict = {}
    for a in assessments:
        code = a.bncc_code
        if code not in by_skill:
            by_skill[code] = []
        if a.level_assigned:
            by_skill[code].append(a.level_assigned)

    radar_data = []
    for code, levels in by_skill.items():
        avg = round(sum(levels) / len(levels), 2) if levels else 0
        radar_data.append({"bncc_code": code, "average": avg, "count": len(levels)})

    return {"class_name": class_name, "data": radar_data}
