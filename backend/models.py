from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    must_change_password = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SetupClass(Base):
    __tablename__ = "setup_classes"
    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Student(Base):
    __tablename__ = "students"
    student_id = Column(String, primary_key=True)
    student_name = Column(String, nullable=False)
    # Refere a Column class_name em setup_classes, mas usualmente é melhor relacionar, 
    # porém o schema usouREFERENCES public.setup_classes(class_name). 
    class_name = Column(String, ForeignKey("setup_classes.class_name"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SetupDiscipline(Base):
    __tablename__ = "setup_disciplines"
    id = Column(Integer, primary_key=True, index=True)
    discipline_name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BnccLibrary(Base):
    __tablename__ = "bncc_library"
    bncc_code = Column(String, primary_key=True, index=True)
    skill_description = Column(Text, nullable=False)
    discipline_id = Column(Integer, ForeignKey("setup_disciplines.id"))
    bimester = Column(String)
    grade = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TeacherRubric(Base):
    __tablename__ = "teacher_rubrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rubric_id = Column(String, unique=True, nullable=False)
    bncc_code = Column(String, nullable=False)
    objective = Column(Text, nullable=False)
    level_1_desc = Column(Text)
    level_2_desc = Column(Text)
    level_3_desc = Column(Text)
    level_4_desc = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Assessment(Base):
    __tablename__ = "assessments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(String, ForeignKey("students.student_id"))
    rubric_id = Column(String, ForeignKey("teacher_rubrics.rubric_id"))
    bncc_code = Column(String, nullable=False)
    level_assigned = Column(Integer)
    date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
