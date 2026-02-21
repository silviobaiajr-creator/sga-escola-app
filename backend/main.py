from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import pandas as pd

from .database import engine, Base, get_db
from . import models, schemas
from .services import ai_service, analytics_service

# Cria as tabelas ausentes (caso existam, mas no Supabase já existem as principais)
# models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SGA-H API",
    description="Backend API for SGA-H School Management System",
    version="1.0.0"
)

# CORS — aceita localhost em dev e URLs Vercel em produção
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
] + [o.strip() for o in ALLOWED_ORIGINS if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # aceita qualquer URL Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root(db: Session = Depends(get_db)):
    # Test DB connection
    try:
        count = db.query(models.User).count()
        db_status = f"Connected (Users count: {count})"
    except Exception as e:
        db_status = f"Error: {e}"
        
    return {"message": "SGA-H API is running!", "database": db_status}

@app.get("/api/students")
def get_students(
    db: Session = Depends(get_db),
    limit: int = 100,
    class_name: str = None
):
    query = db.query(models.Student)
    if class_name:
        query = query.filter(models.Student.class_name == class_name)
    students = query.limit(limit).all()
    return [
        {"id": s.student_id, "name": s.student_name, "class_name": s.class_name}
        for s in students
    ]

@app.get("/api/classes")
def get_classes(db: Session = Depends(get_db)):
    classes = db.query(models.SetupClass).all()
    return [{"name": c.class_name, "grade": c.grade, "year": c.year} for c in classes]

@app.get("/api/disciplines")
def get_disciplines(db: Session = Depends(get_db)):
    disciplines = db.query(models.SetupDiscipline).all()
    return [{"id": d.id, "name": d.name, "abbreviation": d.abbreviation} for d in disciplines]

@app.get("/api/bncc-skills")
def get_bncc_skills(
    db: Session = Depends(get_db),
    discipline_id: int = None,
    limit: int = 50
):
    query = db.query(models.BnccLibrary)
    if discipline_id:
        query = query.filter(models.BnccLibrary.discipline_id == discipline_id)
    skills = query.limit(limit).all()
    return [
        {
            "id": s.id,
            "bncc_code": s.bncc_code,
            "description": s.description,
            "discipline_id": s.discipline_id,
            "grade": s.grade,
            "bimester": s.bimester,
        }
        for s in skills
    ]

@app.get("/api/assessments")
def get_assessments(
    db: Session = Depends(get_db),
    class_name: str = None,
    limit: int = 500
):
    query = db.query(models.Assessment).join(
        models.Student, models.Assessment.student_id == models.Student.student_id
    )
    if class_name:
        query = query.filter(models.Student.class_name == class_name)
    assessments = query.limit(limit).all()
    return [
        {
            "id": str(a.assessment_id),
            "student_id": a.student_id,
            "rubric_id": str(a.rubric_id),
            "level_assigned": a.level_assigned,
            "date": str(a.date) if a.date else None,
        }
        for a in assessments
    ]

# --- AI ROUTES ---
@app.post("/api/ai/objectives")
def generate_lesson_objectives(req: schemas.AIObjectivesRequest):
    result = ai_service.generate_objectives(
        skill_code=req.skill_code,
        skill_description=req.skill_description,
        quantity=req.quantity,
        discipline_name=req.discipline_name
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/ai/rubric")
def generate_rubric(req: schemas.AIRubricRequest):
    result = ai_service.generate_rubric(
        skill_code=req.skill_code,
        objective=req.objective
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

# --- ANALYTICS ROUTES ---
@app.post("/api/analytics/heatmap")
def get_heatmap_data(req: schemas.HeatmapRequest):
    if not req.assessments:
        return {"data": []}
        
    df = pd.DataFrame([a.dict() for a in req.assessments])
    df_calc = analytics_service.calcular_notas(df)
    
    # Converter para lista de dicionários p/ JSON
    if df_calc.empty:
        return {"data": []}
    
    return {"data": df_calc.to_dict(orient="records")}

@app.get("/health")
def health_check():
    return {"status": "ok"}

