from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class AIObjectivesRequest(BaseModel):
    skill_code: str
    skill_description: str
    quantity: int = 3
    discipline_name: Optional[str] = None

class AIRubricRequest(BaseModel):
    skill_code: str
    objective: str

class AssessmentRecord(BaseModel):
    student_id: str
    rubric_id: str
    bncc_code: str
    level_assigned: float
    date: str
    class_name: Optional[str] = None
    student_name: Optional[str] = None

class HeatmapRequest(BaseModel):
    assessments: List[AssessmentRecord]

class AssessmentBatchItem(BaseModel):
    student_id: str
    bncc_code: str
    level_assigned: int
    bimester: int
    class_name: Optional[str] = None
    discipline_id: Optional[int] = None
    teacher_id: Optional[UUID] = None
    date: datetime
    objective_id: UUID
