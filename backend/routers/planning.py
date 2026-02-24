"""
Rotas de Planejamento Pedagógico
- Gerenciar o planejamento BNCC por bimestre/ano_escolar
- Objetivos de aprendizagem com workflow de aprovação
- Rubricas (4 níveis) com workflow de aprovação
- Regras de negócio: aprovação automática com 1 professor, bloqueio de regerar
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import uuid as _uuid

from ..database import get_db
from .. import models
from ..services import ai_service

router = APIRouter(prefix="/api/planning", tags=["planning"])


# ─────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────

class PlanningCreate(BaseModel):
    bncc_code: str
    discipline_id: int
    year_level: int
    bimester: int
    school_year: Optional[int] = None
    teacher_id: Optional[str] = None

class ObjectiveUpdate(BaseModel):
    description: str
    teacher_id: str
    notes: Optional[str] = None

class ApprovalAction(BaseModel):
    teacher_id: str
    action: str         # approved | rejected | edited
    new_description: Optional[str] = None
    notes: Optional[str] = None

class GenerateObjectivesRequest(BaseModel):
    bncc_code: str
    discipline_id: int
    year_level: int
    bimester: int
    quantity: int = 3
    teacher_id: str


# ─────────────────────────────────────────
# PLANEJAMENTO BIMESTRAL
# ─────────────────────────────────────────

@router.get("/bimester")
def list_planning(
    discipline_id: int,
    year_level: int,
    bimester: Optional[int] = None,
    school_year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    from datetime import datetime
    sy = school_year or datetime.now().year
    q = db.query(models.PlanningBimester).filter_by(
        discipline_id=discipline_id,
        year_level=year_level,
        school_year=sy
    )
    if bimester:
        q = q.filter_by(bimester=bimester)
    rows = q.all()
    return [
        {
            "id": str(r.id), "bncc_code": r.bncc_code,
            "discipline_id": r.discipline_id, "year_level": r.year_level,
            "bimester": r.bimester, "school_year": r.school_year,
            "skill_description": r.bncc_skill.skill_description if r.bncc_skill else None,
        }
        for r in rows
    ]

@router.post("/bimester", status_code=201)
def add_to_planning(body: PlanningCreate, db: Session = Depends(get_db)):
    from datetime import datetime
    obj = models.PlanningBimester(
        bncc_code=body.bncc_code,
        discipline_id=body.discipline_id,
        year_level=body.year_level,
        bimester=body.bimester,
        school_year=body.school_year or datetime.now().year,
        teacher_id=_uuid.UUID(body.teacher_id) if body.teacher_id else None
    )
    db.add(obj)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Habilidade já planejada para este bimestre.")
    return {"id": str(obj.id)}

@router.delete("/bimester/{planning_id}")
def remove_from_planning(planning_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.PlanningBimester).get(_uuid.UUID(planning_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Planejamento não encontrado.")
    db.delete(obj); db.commit()
    return {"ok": True}


# ─────────────────────────────────────────
# OBJETIVOS DE APRENDIZAGEM
# ─────────────────────────────────────────

def _count_teachers_for_discipline(db: Session, discipline_id: int, year_level: int) -> int:
    """Conta os professores únicos vinculados à disciplina em turmas do mesmo ano."""
    classes = db.query(models.SetupClass).filter_by(year_level=year_level).all()
    class_ids = [c.id for c in classes]
    if not class_ids:
        return 0
    count = db.query(models.TeacherClassDiscipline).filter(
        models.TeacherClassDiscipline.discipline_id == discipline_id,
        models.TeacherClassDiscipline.class_id.in_(class_ids)
    ).distinct(models.TeacherClassDiscipline.teacher_id).count()
    return count


@router.get("/objectives")
def list_objectives(
    discipline_id: int,
    year_level: int,
    bimester: int,
    bncc_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.LearningObjective).filter_by(
        discipline_id=discipline_id,
        year_level=year_level,
        bimester=bimester
    )
    
    if bncc_code and bncc_code != "_all":
        q = q.filter_by(bncc_code=bncc_code)
        
    rows = q.order_by(models.LearningObjective.order_index).all()

    result = []
    for r in rows:
        approvals = [
            {
                "teacher_id": str(a.teacher_id), 
                "teacher_name": a.teacher.full_name or a.teacher.username if a.teacher else "Desconhecido",
                "action": a.action,
                "notes": a.notes, 
                "created_at": str(a.created_at),
                "previous_description": a.previous_description
            }
            for a in r.approvals
        ]
        has_rubrics = len(r.rubric_levels) > 0
        result.append({
            "id": str(r.id), "description": r.description,
            "order_index": r.order_index, "status": r.status,
            "ai_explanation": r.ai_explanation,
            "bncc_code": r.bncc_code,
            "bncc_description": r.bncc_skill.skill_description if r.bncc_skill else "",
            "has_rubrics": has_rubrics,
            "rubrics_status": r.rubric_levels[0].status if has_rubrics else None,
            "approvals": approvals,
        })
    return result


@router.post("/objectives/generate")
def generate_objectives(body: GenerateObjectivesRequest, db: Session = Depends(get_db)):
    """
    Gera objetivos via IA e salva como 'draft'.
    Regra: Uma habilidade BNCC só pode gerar objetivos UMA VEZ para a escola toda (por disciplina).
    """
    existing_objectives = db.query(models.LearningObjective).filter_by(
        bncc_code=body.bncc_code,
        discipline_id=body.discipline_id
    ).count()

    if existing_objectives > 0:
        raise HTTPException(
            status_code=409,
            detail="Os objetivos de aprendizagem para esta habilidade já foram gerados. Eles são comuns para toda a escola."
        )

    # Buscar a habilidade BNCC
    skill = db.query(models.BnccLibrary).get(body.bncc_code)
    if not skill:
        raise HTTPException(status_code=404, detail="Habilidade BNCC não encontrada.")

    # Buscar competências específicas da disciplina
    competencies = db.query(models.SpecificCompetency).filter(
        models.SpecificCompetency.discipline_id == body.discipline_id,
        (models.SpecificCompetency.year_grade == body.year_level) |
        (models.SpecificCompetency.year_grade == None)
    ).order_by(models.SpecificCompetency.competency_number).all()

    discipline = db.query(models.SetupDiscipline).get(body.discipline_id)
    disc_name  = discipline.discipline_name if discipline else "Geral"
    comp_list  = [f"{c.competency_number}. {c.description}" for c in competencies]

    # Gerar via IA
    result = ai_service.generate_objectives(
        skill_code=body.bncc_code,
        skill_description=skill.skill_description,
        quantity=body.quantity,
        discipline_name=disc_name,
        specific_competencies=comp_list,
        bimester=body.bimester,
        year_level=body.year_level
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # Deletar drafts anteriores (regera rascunho já existente)
    db.query(models.LearningObjective).filter_by(
        bncc_code=body.bncc_code,
        discipline_id=body.discipline_id,
        year_level=body.year_level,
        bimester=body.bimester,
        status="draft"
    ).delete()

    # Salvar novos objetivos como draft
    objectives_list  = result.get("objectives", [])
    explanations     = result.get("explanations", [])
    global_explanation = result.get("explanation", "")
    teacher_uuid = _uuid.UUID(body.teacher_id)

    created_ids = []
    for idx, obj_desc in enumerate(objectives_list):
        explanation = explanations[idx] if idx < len(explanations) else global_explanation
        obj = models.LearningObjective(
            bncc_code=body.bncc_code,
            discipline_id=body.discipline_id,
            year_level=body.year_level,
            bimester=body.bimester,
            description=obj_desc,
            order_index=idx + 1,
            ai_explanation=explanation,
            status="draft",
            created_by=teacher_uuid
        )
        db.add(obj)
        db.flush()
        created_ids.append(str(obj.id))

    db.commit()
    return {
        "objectives": objectives_list,
        "explanations": explanations,
        "explanation": global_explanation,
        "draft_ids": created_ids
    }


@router.put("/objectives/{objective_id}")
def update_objective(
    objective_id: str,
    body: ObjectiveUpdate,
    db: Session = Depends(get_db)
):
    """Editar um objetivo — invalida aprovações anteriores (regra #9)."""
    obj = db.query(models.LearningObjective).get(_uuid.UUID(objective_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Objetivo não encontrado.")

    # Registrar a edição no histórico
    history = models.ObjectiveApproval(
        objective_id=obj.id,
        teacher_id=_uuid.UUID(body.teacher_id),
        action="edited",
        previous_description=obj.description,
        notes=body.notes
    )
    db.add(history)

    # Atualizar descrição e resetar status
    obj.description = body.description
    obj.status = "pending"  # Voltar para pendente (re-aprovação obrigatória)
    db.commit()
    return {"ok": True, "new_status": "pending"}


@router.post("/objectives/{objective_id}/approve")
def approve_objective(
    objective_id: str,
    body: ApprovalAction,
    db: Session = Depends(get_db)
):
    """
    Aprovar/rejeitar/editar um objetivo.
    Regra #14: Se só há 1 professor na disciplina, a aprovação é automática.
    """
    obj = db.query(models.LearningObjective).get(_uuid.UUID(objective_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Objetivo não encontrado.")

    teacher_uuid   = _uuid.UUID(body.teacher_id)
    teacher_count  = _count_teachers_for_discipline(db, obj.discipline_id, obj.year_level)

    if body.action == "edited" and body.new_description:
        history = models.ObjectiveApproval(
            objective_id=obj.id, teacher_id=teacher_uuid, action="edited",
            previous_description=obj.description, notes=body.notes
        )
        db.add(history)
        obj.description = body.new_description
        obj.status = "pending"
        db.commit()
        return {"ok": True, "status": "pending", "message": "Editado. Aguarda re-aprovação."}

    # Registrar aprovação/rejeição
    history = models.ObjectiveApproval(
        objective_id=obj.id, teacher_id=teacher_uuid,
        action=body.action, notes=body.notes
    )
    db.add(history)

    if body.action == "approved":
        # Identificar a última edição para invalidar aprovações antigas
        edits = [a for a in obj.approvals if a.action == "edited" and a.created_at is not None]
        last_edit_time = max([e.created_at for e in edits]) if edits else None

        valid_approvals = set()
        for a in obj.approvals:
            if a.action == "approved" and a.created_at is not None:
                if not last_edit_time or a.created_at >= last_edit_time:
                    valid_approvals.add(str(a.teacher_id))
                    
        valid_approvals.add(str(body.teacher_id))

        if teacher_count <= 1 or len(valid_approvals) >= teacher_count:
            obj.status = "approved"
            message = "Aprovado!"
        else:
            obj.status = "pending"
            message = f"Aprovação registrada. Aguardando {teacher_count - len(valid_approvals)} professor(es)."
    else:
        obj.status = "rejected"
        message = "Objetivo rejeitado."

    db.commit()
    return {"ok": True, "status": obj.status, "message": message}


@router.post("/objectives/{objective_id}/submit")
def submit_for_approval(objective_id: str, db: Session = Depends(get_db)):
    """Enviar objetivo de 'draft' para 'pending' (aguardando aprovação)."""
    obj = db.query(models.LearningObjective).get(_uuid.UUID(objective_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Objetivo não encontrado.")
    if obj.status != "draft":
        raise HTTPException(status_code=400, detail="Apenas objetivos em rascunho podem ser submetidos.")
    
    # Regra #1: Auto-Aprovação do Criador ao "Salvar"
    if obj.created_by:
        history = models.ObjectiveApproval(
            objective_id=obj.id,
            teacher_id=obj.created_by,
            action="approved",
            notes="Auto-aprovado na submissão (Criador)"
        )
        db.add(history)
        
        teacher_count = _count_teachers_for_discipline(db, obj.discipline_id, obj.year_level)
        if teacher_count <= 1:
            obj.status = "approved"
        else:
            obj.status = "pending"
    else:
        obj.status = "pending"
        
    db.commit()
    return {"ok": True, "status": obj.status}


# ─────────────────────────────────────────
# RUBRICAS
# ─────────────────────────────────────────

@router.get("/rubrics/{objective_id}")
def get_rubrics(objective_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.LearningObjective).get(_uuid.UUID(objective_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Objetivo não encontrado.")
    levels = sorted(obj.rubric_levels, key=lambda r: r.level)
    return [
        {
            "id": str(r.id), "level": r.level, "description": r.description,
            "status": r.status,
            "approvals": [
                {
                    "teacher_id": str(a.teacher_id), 
                    "teacher_name": a.teacher.full_name or a.teacher.username if a.teacher else "Desconhecido",
                    "action": a.action,
                    "notes": a.notes, 
                    "created_at": str(a.created_at),
                    "previous_description": a.previous_description
                }
                for a in r.approvals
            ]
        }
        for r in levels
    ]


@router.post("/rubrics/{objective_id}/generate")
def generate_rubrics(
    objective_id: str,
    body: dict,
    db: Session = Depends(get_db)
):
    """
    Gera os 4 níveis de rubrica para um objetivo via IA.
    Regra #15: Bloqueia se já houver rubricas pendentes ou aprovadas.
    """
    obj = db.query(models.LearningObjective).get(_uuid.UUID(objective_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Objetivo não encontrado.")

    existing = db.query(models.RubricLevel).filter_by(objective_id=obj.id).first()
    if existing and existing.status in ("pending", "approved"):
        raise HTTPException(
            status_code=409,
            detail="Rubricas já existem para este objetivo. Edite as rubricas existentes."
        )

    teacher_id = body.get("teacher_id")
    skill = db.query(models.BnccLibrary).get(obj.bncc_code)

    result = ai_service.generate_rubric(
        skill_code=obj.bncc_code,
        objective=obj.description
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # Deletar rubricas antigas (rejected/draft)
    db.query(models.RubricLevel).filter_by(objective_id=obj.id).delete()

    teacher_count = _count_teachers_for_discipline(db, obj.discipline_id, obj.year_level)
    rubric = result.get("rubric", {})

    for level_num in [1, 2, 3, 4]:
        desc = rubric.get(str(level_num), "")
        if not desc:
            continue
            
        teacher_uuid = _uuid.UUID(teacher_id) if teacher_id else None
        
        rl = models.RubricLevel(
            objective_id=obj.id,
            level=level_num,
            description=desc,
            status="pending",
            created_by=teacher_uuid
        )
        db.add(rl)
        db.flush()
        
        # Auto-aprovar para o criador
        if teacher_uuid:
            history = models.RubricApproval(
                rubric_level_id=rl.id, teacher_id=teacher_uuid,
                action="approved", notes="Auto-aprovado na geração (Criador)"
            )
            db.add(history)
            
            if teacher_count <= 1:
                rl.status = "approved"
            else:
                rl.status = "pending"
        else:
            rl.status = "approved" if teacher_count <= 1 else "pending"

    db.commit()
    return {"ok": True, "levels": rubric}


@router.put("/rubrics/level/{rubric_level_id}")
def update_rubric_level(
    rubric_level_id: str,
    body: ApprovalAction,
    db: Session = Depends(get_db)
):
    rl = db.query(models.RubricLevel).get(_uuid.UUID(rubric_level_id))
    if not rl:
        raise HTTPException(status_code=404, detail="Rubrica não encontrada.")

    teacher_uuid = _uuid.UUID(body.teacher_id)

    if body.action == "edited" and body.new_description:
        history = models.RubricApproval(
            rubric_level_id=rl.id, teacher_id=teacher_uuid,
            action="edited", previous_description=rl.description, notes=body.notes
        )
        db.add(history)
        rl.description = body.new_description
        rl.status = "pending"
        db.commit()
        return {"ok": True, "status": "pending"}

    history = models.RubricApproval(
        rubric_level_id=rl.id, teacher_id=teacher_uuid,
        action=body.action, notes=body.notes
    )
    db.add(history)

    obj = rl.objective
    teacher_count = _count_teachers_for_discipline(db, obj.discipline_id, obj.year_level)

    if body.action == "approved":
        # Identificar a última edição para invalidar antigas
        edits = [a for a in rl.approvals if a.action == "edited" and a.created_at is not None]
        last_edit_time = max([e.created_at for e in edits]) if edits else None

        valid_approvals = set()
        for a in rl.approvals:
            if a.action == "approved" and a.created_at is not None:
                if not last_edit_time or a.created_at >= last_edit_time:
                    valid_approvals.add(str(a.teacher_id))
                    
        valid_approvals.add(str(body.teacher_id))

        if teacher_count <= 1 or len(valid_approvals) >= teacher_count:
            rl.status = "approved"
        else:
            rl.status = "pending"
    else:
        rl.status = "rejected"

    db.commit()
    return {"ok": True, "status": rl.status}
