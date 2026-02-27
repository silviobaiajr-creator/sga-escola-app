import requests
import uuid
import json

url = "https://sga-h-api-377936686920.us-central1.run.app/api/assessments/batch"
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
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    print("STATUS:", response.status_code)
    print("BODY:", response.text)
except Exception as e:
    print("ERROR:", e)
