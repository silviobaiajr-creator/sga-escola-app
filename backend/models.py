from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date,
    ForeignKey, Boolean, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base


# ─────────────────────────────────────────
# TABELAS EXISTENTES (esquema v1 atualizado)
# ─────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username             = Column(String, unique=True, nullable=False)
    password             = Column(String, nullable=False)
    full_name            = Column(String)
    email                = Column(String, unique=True)
    role                 = Column(String, default="teacher")   # admin | coordinator | teacher
    is_active            = Column(Boolean, default=True)
    avatar_url           = Column(String)
    must_change_password = Column(Boolean, default=False)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    class_disciplines    = relationship("TeacherClassDiscipline", back_populates="teacher")
    created_objectives   = relationship("LearningObjective", back_populates="creator")


class SetupClass(Base):
    __tablename__ = "setup_classes"
    id          = Column(Integer, primary_key=True, index=True)
    class_name  = Column(String, unique=True, nullable=False)
    year_level  = Column(Integer)                  # 6, 7, 8, 9
    school_year = Column(Integer)
    shift       = Column(String, default="morning")  # morning | afternoon | evening
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    students    = relationship("Student", back_populates="school_class",
                               foreign_keys="Student.class_name",
                               primaryjoin="SetupClass.class_name == Student.class_name")


class Student(Base):
    __tablename__ = "students"
    student_id        = Column(String, primary_key=True)
    student_name      = Column(String, nullable=False)
    class_name        = Column(String, ForeignKey("setup_classes.class_name"))
    birth_date        = Column(Date)
    enrollment_number = Column(String, unique=True)
    status            = Column(String, default="active")   # active | transferred | inactive
    created_at        = Column(DateTime(timezone=True), server_default=func.now())

    school_class      = relationship("SetupClass", back_populates="students",
                                     foreign_keys=[class_name])
    assessments       = relationship("Assessment", back_populates="student")


class SetupDiscipline(Base):
    __tablename__ = "setup_disciplines"
    id              = Column(Integer, primary_key=True, index=True)
    discipline_name = Column(String, unique=True, nullable=False)
    abbreviation    = Column(String)
    color_code      = Column(String, default="#6366f1")
    area            = Column(String)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    competencies    = relationship("SpecificCompetency", back_populates="discipline")
    bncc_skills     = relationship("BnccLibrary", back_populates="discipline")


class BnccLibrary(Base):
    __tablename__ = "bncc_library"
    bncc_code            = Column(String, primary_key=True, index=True)
    skill_description    = Column(Text, nullable=False)
    discipline_id        = Column(Integer, ForeignKey("setup_disciplines.id"))
    bimester             = Column(String)
    grade                = Column(String)   # kept for legacy
    year_grade           = Column(Integer)  # 6, 7, 8, 9 (BNCC year)
    area                 = Column(String)
    object_of_knowledge  = Column(Text)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())

    discipline           = relationship("SetupDiscipline", back_populates="bncc_skills")
    objectives           = relationship("LearningObjective", back_populates="bncc_skill")
    planning             = relationship("PlanningBimester", back_populates="bncc_skill")


class TeacherRubric(Base):
    """Tabela legada — manter para compatibilidade com avaliações antigas."""
    __tablename__ = "teacher_rubrics"
    id                    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rubric_id             = Column(String, unique=True, nullable=False)
    bncc_code             = Column(String, nullable=False)
    objective             = Column(Text, nullable=False)
    level_1_desc          = Column(Text)
    level_2_desc          = Column(Text)
    level_3_desc          = Column(Text)
    level_4_desc          = Column(Text)
    discipline_id         = Column(Integer, ForeignKey("setup_disciplines.id"))
    bimester              = Column(Integer)
    status                = Column(String, default="pending")
    objective_explanation = Column(Text)
    approved_at           = Column(DateTime(timezone=True))
    created_by            = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at            = Column(DateTime(timezone=True), server_default=func.now())

    assessments           = relationship("Assessment", back_populates="rubric")


class Assessment(Base):
    __tablename__ = "assessments"
    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id     = Column(String, ForeignKey("students.student_id"))
    rubric_id      = Column(String, ForeignKey("teacher_rubrics.rubric_id"))
    bncc_code      = Column(String, nullable=False)
    level_assigned = Column(Integer)
    date           = Column(DateTime(timezone=True))
    bimester       = Column(Integer)
    class_name     = Column(String)
    discipline_id  = Column(Integer, ForeignKey("setup_disciplines.id"))
    teacher_id     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    objective_id   = Column(UUID(as_uuid=True), ForeignKey("learning_objectives.id"))
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    student        = relationship("Student", back_populates="assessments")
    rubric         = relationship("TeacherRubric", back_populates="assessments")
    objective      = relationship("LearningObjective", back_populates="assessments")


# ─────────────────────────────────────────
# NOVAS TABELAS (esquema v2)
# ─────────────────────────────────────────

class SpecificCompetency(Base):
    """Competências específicas de uma disciplina (BNCC).
    Usadas como contexto nos prompts do Vertex AI."""
    __tablename__ = "specific_competencies"
    id                 = Column(Integer, primary_key=True, index=True)
    discipline_id      = Column(Integer, ForeignKey("setup_disciplines.id"), nullable=False)
    year_grade         = Column(Integer)   # NULL = válido para todos os anos
    competency_number  = Column(Integer, nullable=False)
    description        = Column(Text, nullable=False)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())

    discipline         = relationship("SetupDiscipline", back_populates="competencies")


class LearningObjective(Base):
    """Objetivos de aprendizagem vinculados a uma habilidade BNCC.
    Planejamento por ANO ESCOLAR + BIMESTRE (todas as turmas do mesmo ano compartilham)."""
    __tablename__ = "learning_objectives"
    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bncc_code      = Column(String, ForeignKey("bncc_library.bncc_code"), nullable=False)
    discipline_id  = Column(Integer, ForeignKey("setup_disciplines.id"))
    year_level     = Column(Integer, nullable=False)   # 6, 7, 8, 9
    bimester       = Column(Integer, nullable=False)   # 1-4
    description    = Column(Text, nullable=False)
    order_index    = Column(Integer, nullable=False, default=1)
    ai_explanation = Column(Text)
    status         = Column(String, default="draft")   # draft | pending | approved | rejected
    created_by     = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bncc_skill     = relationship("BnccLibrary", back_populates="objectives")
    creator        = relationship("User", back_populates="created_objectives")
    rubric_levels  = relationship("RubricLevel", back_populates="objective", cascade="all, delete-orphan")
    approvals      = relationship("ObjectiveApproval", back_populates="objective", cascade="all, delete-orphan")
    assessments    = relationship("Assessment", back_populates="objective")


class RubricLevel(Base):
    """4 níveis da rubrica de avaliação de um objetivo."""
    __tablename__ = "rubric_levels"
    __table_args__ = (UniqueConstraint("objective_id", "level", name="uq_rubric_objective_level"),)

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    objective_id = Column(UUID(as_uuid=True), ForeignKey("learning_objectives.id"), nullable=False)
    level        = Column(Integer, nullable=False)   # 1-4
    description  = Column(Text, nullable=False)
    status       = Column(String, default="pending")  # pending | approved | rejected
    created_by   = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    objective    = relationship("LearningObjective", back_populates="rubric_levels")
    approvals    = relationship("RubricApproval", back_populates="rubric_level", cascade="all, delete-orphan")


class ObjectiveApproval(Base):
    """Histórico de aprovações/rejeições/edições de um objetivo."""
    __tablename__ = "objective_approvals"
    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    objective_id         = Column(UUID(as_uuid=True), ForeignKey("learning_objectives.id"), nullable=False)
    teacher_id           = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action               = Column(String, nullable=False)   # approved | rejected | edited
    previous_description = Column(Text)
    notes                = Column(Text)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())

    objective            = relationship("LearningObjective", back_populates="approvals")
    teacher              = relationship("User")


class RubricApproval(Base):
    """Histórico de aprovações de rubricas."""
    __tablename__ = "rubric_approvals"
    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rubric_level_id      = Column(UUID(as_uuid=True), ForeignKey("rubric_levels.id"), nullable=False)
    teacher_id           = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action               = Column(String, nullable=False)
    previous_description = Column(Text)
    notes                = Column(Text)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())

    rubric_level         = relationship("RubricLevel", back_populates="approvals")
    teacher              = relationship("User")


class TeacherClassDiscipline(Base):
    """Vínculo M:N entre Professor, Turma e Disciplina."""
    __tablename__ = "teacher_class_discipline"
    __table_args__ = (
        UniqueConstraint("teacher_id", "class_id", "discipline_id", "school_year",
                         name="uq_teacher_class_discipline_year"),
    )
    id            = Column(Integer, primary_key=True)
    teacher_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    class_id      = Column(Integer, ForeignKey("setup_classes.id"), nullable=False)
    discipline_id = Column(Integer, ForeignKey("setup_disciplines.id"), nullable=False)
    school_year   = Column(Integer)

    teacher       = relationship("User", back_populates="class_disciplines")
    school_class  = relationship("SetupClass")
    discipline    = relationship("SetupDiscipline")


class PlanningBimester(Base):
    """Planejamento: habilidade BNCC → ano_escolar + bimestre.
    Todas as turmas do mesmo ano compartilham o mesmo planejamento."""
    __tablename__ = "planning_bimester"
    __table_args__ = (
        UniqueConstraint("bncc_code", "discipline_id", "year_level", "bimester", "school_year",
                         name="uq_planning_unique"),
    )
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bncc_code     = Column(String, ForeignKey("bncc_library.bncc_code"), nullable=False)
    discipline_id = Column(Integer, ForeignKey("setup_disciplines.id"), nullable=False)
    year_level    = Column(Integer, nullable=False)
    bimester      = Column(Integer, nullable=False)
    school_year   = Column(Integer)
    teacher_id    = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    bncc_skill    = relationship("BnccLibrary", back_populates="planning")
    teacher       = relationship("User")
    discipline    = relationship("SetupDiscipline")
