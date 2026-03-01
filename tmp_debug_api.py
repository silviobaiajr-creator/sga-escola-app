from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.abspath("backend"))
from backend.main import app

client = TestClient(app)

def test():
    # Calling the objectives endpoint for discipline 1, year 6, bimester 1
    response = client.get("/api/planning/objectives", params={
        "discipline_id": 1,
        "year_level": 6,
        "bimester": 1,
        "bncc_code": "_all"
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total objetivos returned API: {len(data)}")
        for o in data:
            print(f"Obj ID: {o['id']} | Status: {o['status']} | BNCC: {o.get('bncc_code')}")
            print(f"Has Rubrics: {o.get('has_rubrics')} | Rubrics Status: {o.get('rubrics_status')}")
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    test()
