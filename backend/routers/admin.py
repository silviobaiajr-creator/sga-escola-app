"""
Rotas de Administração — Gerenciar turmas, disciplinas, usuários,
competências específicas, vínculos professor-turma e upload CSV de alunos.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import csv, io

from ..database import get_db
from .. import models

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─────────────────────────────────────────
# SCHEMAS LOCAIS
# ─────────────────────────────────────────

class ClassCreate(BaseModel):
    class_name: str
    year_level: Optional[int] = None
    school_year: Optional[int] = None
    shift: Optional[str] = "morning"

class DisciplineCreate(BaseModel):
    discipline_name: str
    abbreviation: Optional[str] = None
    color_code: Optional[str] = "#6366f1"
    area: Optional[str] = None

class CompetencyCreate(BaseModel):
    discipline_id: int
    year_grade: Optional[int] = None
    competency_number: int
    description: str

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = "teacher"

class TeacherClassCreate(BaseModel):
    teacher_id: str
    class_id: int
    discipline_id: int
    school_year: Optional[int] = None


# ─────────────────────────────────────────
# TURMAS
# ─────────────────────────────────────────

@router.get("/classes")
def list_classes(db: Session = Depends(get_db)):
    rows = db.query(models.SetupClass).order_by(models.SetupClass.class_name).all()
    return [
        {
            "id": r.id, "class_name": r.class_name,
            "year_level": r.year_level, "school_year": r.school_year,
            "shift": r.shift
        }
        for r in rows
    ]

@router.post("/classes", status_code=status.HTTP_201_CREATED)
def create_class(body: ClassCreate, db: Session = Depends(get_db)):
    existing = db.query(models.SetupClass).filter_by(class_name=body.class_name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Turma já cadastrada.")
    obj = models.SetupClass(**body.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return {"id": obj.id, "class_name": obj.class_name}

@router.put("/classes/{class_id}")
def update_class(class_id: int, body: ClassCreate, db: Session = Depends(get_db)):
    obj = db.query(models.SetupClass).get(class_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    for k, v in body.dict(exclude_none=True).items():
        setattr(obj, k, v)
    db.commit(); return {"ok": True}

@router.delete("/classes/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.SetupClass).get(class_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    db.delete(obj); db.commit()
    return {"ok": True}


# ─────────────────────────────────────────
# DISCIPLINAS
# ─────────────────────────────────────────

@router.get("/disciplines")
def list_disciplines(db: Session = Depends(get_db)):
    rows = db.query(models.SetupDiscipline).order_by(models.SetupDiscipline.discipline_name).all()
    return [
        {
            "id": r.id, "name": r.discipline_name,
            "abbreviation": r.abbreviation, "color_code": r.color_code, "area": r.area
        }
        for r in rows
    ]

@router.post("/disciplines", status_code=201)
def create_discipline(body: DisciplineCreate, db: Session = Depends(get_db)):
    obj = models.SetupDiscipline(**body.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return {"id": obj.id, "name": obj.discipline_name}

@router.put("/disciplines/{disc_id}")
def update_discipline(disc_id: int, body: DisciplineCreate, db: Session = Depends(get_db)):
    obj = db.query(models.SetupDiscipline).get(disc_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada.")
    for k, v in body.dict(exclude_none=True).items():
        if k == "discipline_name": obj.discipline_name = v
        else: setattr(obj, k, v)
    db.commit(); return {"ok": True}

@router.delete("/disciplines/{disc_id}")
def delete_discipline(disc_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.SetupDiscipline).get(disc_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada.")
    db.delete(obj); db.commit(); return {"ok": True}


# ─────────────────────────────────────────
# COMPETÊNCIAS ESPECÍFICAS
# ─────────────────────────────────────────

@router.get("/competencies")
def list_competencies(
    discipline_id: Optional[int] = None,
    year_grade: Optional[int] = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.SpecificCompetency)
    if discipline_id:
        q = q.filter_by(discipline_id=discipline_id)
    if year_grade:
        q = q.filter(
            (models.SpecificCompetency.year_grade == year_grade) |
            (models.SpecificCompetency.year_grade == None)
        )
    rows = q.order_by(models.SpecificCompetency.competency_number).all()
    return [
        {
            "id": r.id, "discipline_id": r.discipline_id,
            "year_grade": r.year_grade, "competency_number": r.competency_number,
            "description": r.description
        }
        for r in rows
    ]

@router.post("/competencies", status_code=201)
def create_competency(body: CompetencyCreate, db: Session = Depends(get_db)):
    obj = models.SpecificCompetency(**body.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return {"id": obj.id}

@router.put("/competencies/{comp_id}")
def update_competency(comp_id: int, body: CompetencyCreate, db: Session = Depends(get_db)):
    obj = db.query(models.SpecificCompetency).get(comp_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Competência não encontrada.")
    for k, v in body.dict(exclude_none=True).items():
        setattr(obj, k, v)
    db.commit(); return {"ok": True}

@router.delete("/competencies/{comp_id}")
def delete_competency(comp_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.SpecificCompetency).get(comp_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Competência não encontrada.")
    db.delete(obj); db.commit(); return {"ok": True}


# ─────────────────────────────────────────
# USUÁRIOS / PROFESSORES
# ─────────────────────────────────────────

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    rows = db.query(models.User).order_by(models.User.full_name).all()
    return [
        {
            "id": str(r.id), "username": r.username,
            "full_name": r.full_name, "email": r.email,
            "role": r.role, "is_active": r.is_active
        }
        for r in rows
    ]

@router.post("/users", status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    import hashlib
    hashed = hashlib.sha256(body.password.encode()).hexdigest()
    obj = models.User(
        username=body.username,
        password=hashed,
        full_name=body.full_name,
        email=body.email,
        role=body.role or "teacher",
        must_change_password=True
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return {"id": str(obj.id), "username": obj.username}

@router.put("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: str, db: Session = Depends(get_db)):
    import uuid as _uuid
    obj = db.query(models.User).get(_uuid.UUID(user_id))
    if not obj:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    obj.is_active = not obj.is_active
    db.commit()
    return {"is_active": obj.is_active}


# ─────────────────────────────────────────
# VÍNCULO PROFESSOR – TURMA – DISCIPLINA
# ─────────────────────────────────────────

@router.get("/teacher-class")
def list_teacher_class(db: Session = Depends(get_db)):
    rows = db.query(models.TeacherClassDiscipline).all()
    return [
        {
            "id": r.id,
            "teacher_id": str(r.teacher_id),
            "class_id": r.class_id,
            "discipline_id": r.discipline_id,
            "school_year": r.school_year,
        }
        for r in rows
    ]

@router.post("/teacher-class", status_code=201)
def create_teacher_class(body: TeacherClassCreate, db: Session = Depends(get_db)):
    import uuid as _uuid
    from datetime import datetime
    obj = models.TeacherClassDiscipline(
        teacher_id=_uuid.UUID(body.teacher_id),
        class_id=body.class_id,
        discipline_id=body.discipline_id,
        school_year=body.school_year or datetime.now().year
    )
    db.add(obj)
    try:
        db.commit(); db.refresh(obj)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Vínculo já existe.")
    return {"id": obj.id}

@router.delete("/teacher-class/{link_id}")
def delete_teacher_class(link_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.TeacherClassDiscipline).get(link_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Vínculo não encontrado.")
    db.delete(obj); db.commit(); return {"ok": True}


# ─────────────────────────────────────────
# UPLOAD CSV DE ALUNOS
# ─────────────────────────────────────────

@router.post("/students/upload-csv")
async def upload_students_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    CSV obrigatório: nome, id_aluno, turma
    Colunas opcionais: data_nascimento (YYYY-MM-DD), nr_matricula
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Envie um arquivo .csv")

    content = await file.read()
    decoded = content.decode("utf-8-sig")  # remove BOM se houver
    reader  = csv.DictReader(io.StringIO(decoded))

    inserted = 0
    updated  = 0
    errors   = []

    for i, row in enumerate(reader, start=2):   # linha 2 = primeira linha de dados
        nome    = (row.get("nome") or row.get("student_name") or "").strip()
        id_al   = (row.get("id_aluno") or row.get("student_id") or "").strip()
        turma   = (row.get("turma")  or row.get("class_name") or "").strip()

        if not nome or not id_al or not turma:
            errors.append(f"Linha {i}: campos obrigatórios incompletos (nome, id_aluno, turma).")
            continue

        # Verificar se a turma existe
        cls = db.query(models.SetupClass).filter_by(class_name=turma).first()
        if not cls:
            errors.append(f"Linha {i}: turma '{turma}' não encontrada no sistema.")
            continue

        existing = db.query(models.Student).get(id_al)
        if existing:
            existing.student_name = nome
            existing.class_name   = turma
            if row.get("data_nascimento"):
                try:
                    from datetime import date
                    existing.birth_date = date.fromisoformat(row["data_nascimento"].strip())
                except Exception:
                    pass
            if row.get("nr_matricula"):
                existing.enrollment_number = row["nr_matricula"].strip()
            updated += 1
        else:
            student = models.Student(
                student_id    = id_al,
                student_name  = nome,
                class_name    = turma,
            )
            if row.get("data_nascimento"):
                try:
                    from datetime import date
                    student.birth_date = date.fromisoformat(row["data_nascimento"].strip())
                except Exception:
                    pass
            if row.get("nr_matricula"):
                student.enrollment_number = row["nr_matricula"].strip()
            db.add(student)
            inserted += 1

    db.commit()
    return {
        "inserted": inserted,
        "updated":  updated,
        "errors":   errors,
        "total_processed": inserted + updated
    }
