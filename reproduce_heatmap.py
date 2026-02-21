import pandas as pd
import numpy as np

# Mock Data
def get_mock_students(n=30):
    ids = [str(i) for i in range(1, n+1)]
    # Add some garbage to test robustness if needed, but starting clean first
    names = [f"Student {i}" for i in range(1, n+1)]
    return pd.DataFrame({
        'student_id': ids,
        'student_name': names,
        'class_name': ['9º Ano D'] * n
    })

def get_mock_assessments(students):
    # Only assessments for first 28 students to simulate 2 missing data
    # But we want them in the heatmap (with 0/NaN)
    valid_ids = students['student_id'].tolist()[:28] 
    data = []
    for sid in valid_ids:
        data.append({
            'student_id': sid,
            'bncc_code': 'EF09MA01',
            'level_numeric': 3.5
        })
    return pd.DataFrame(data)

def test_logic():
    print("--- Starting Logic Test ---")
    
    # 1. Setup
    df_students = get_mock_students(30)
    df_assessments = get_mock_assessments(df_students)
    class_filter = "9º Ano D"
    
    # 2. Logic from app.py (Simulated)
    
    # Get Current Class Students (The "30")
    current_class_students = df_students[df_students['class_name'] == class_filter]['student_id'].astype(str).str.replace('.0','').unique().tolist()
    print(f"Total Class Students: {len(current_class_students)}")
    
    # Prepare df_final
    df_final = df_assessments.copy()
    if not df_final.empty:
        df_final['student_id'] = df_final['student_id'].astype(str).str.replace('.0','')
        # logic...
        
    # Pivot
    pivot_table = df_final.pivot_table(
        index='student_id', 
        columns='bncc_code', 
        values='level_numeric',
        aggfunc='mean'
    ).fillna(0)
    
    print(f"Pivot Rows (only with data): {len(pivot_table)}")
    
    # Reindex (The Critical Step)
    if current_class_students:
        pivot_table = pivot_table.reindex(pivot_table.index.union(current_class_students), fill_value=0)
        # Verify Union size
        print(f"Pivot Rows (after Union): {len(pivot_table)}")
        
        # Intersection
        # PROBLEM HYPOTHESIS: If IDs match string-wise perfectly, this works.
        # If there is whitespace mismatch '1 ' vs '1', it fails.
        pivot_table = pivot_table.loc[pivot_table.index.intersection(current_class_students)]
        
    print(f"Final Count: {len(pivot_table)}")
    
    if len(pivot_table) == 30:
        print("✅ SUCCESS: 30 students found.")
    else:
        print(f"❌ FAILURE: Found {len(pivot_table)} students instead of 30.")

if __name__ == "__main__":
    test_logic()
