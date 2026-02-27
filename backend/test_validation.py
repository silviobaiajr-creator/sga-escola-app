import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ValidationError

class AssessmentBatchItem(BaseModel):
    student_id: str
    bncc_code: str
    level_assigned: float
    bimester: int
    class_name: Optional[str] = None
    discipline_id: Optional[int] = None
    teacher_id: Optional[uuid.UUID] = None
    date: datetime
    objective_id: uuid.UUID

payload = [{
    "student_id": "STUDENT-123",
    "bncc_code": "EF06MA01",
    "level_assigned": 3.0,
    "bimester": 1,
    "class_name": "6º Ano A",
    "discipline_id": 1,
    "teacher_id": str(uuid.uuid4()),
    "date": "2026-02-25T22:29:51.123Z",
    "objective_id": str(uuid.uuid4())
}]

try:
    for item in payload:
        validated = AssessmentBatchItem(**item)
        print("Valid:", validated)
except ValidationError as e:
    print("Validation error:", e.json())
