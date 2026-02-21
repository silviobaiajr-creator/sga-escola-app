import pandas as pd
import numpy as np

def test_heatmap_logic():
    print("--- INICIANDO TESTE DA LÓGICA DO MAPA DE CALOR ---")
    
    # 1. MOCK: 30 Alunos na Turma
    # Vamos simular um caso sujo com espaços em branco para provar que o fix funciona
    ids_raw = [f"{i} " for i in range(1, 31)] # IDs com espaço extra!
    names = [f"Aluno {i}" for i in range(1, 31)]
    df_students = pd.DataFrame({
        'student_id': ids_raw, 
        'student_name': names,
        'class_name': ['9º Ano D'] * 30
    })
    
    # 2. MOCK: Avaliações para apenas 28 alunos
    # ids das avaliações podem ou não ter espaço, vamos fazer misturado
    assess_ids = [str(i) for i in range(1, 29)] # IDs limpos (sem espaço)
    data = []
    for sid in assess_ids:
        data.append({
            'student_id': sid,
            'bncc_code': 'EF09MA01',
            'level_numeric': 3.5
        })
    df_assessments = pd.DataFrame(data)
    
    print(f"Alunos na tabela (Simulado): {len(df_students)}")
    print(f"Alunos com nota (Simulado): {len(df_assessments['student_id'].unique())} (Esperado 28)")
    
    # --- APLICANDO A LÓGICA DO APP.PY (CORRIGIDA) ---
    
    # 1. Obter Lista de Alunos da Turma (COM NORMALIZAÇÃO)
    # Codigo original: ...astype(str).replace('.0','').str.strip().unique().tolist()
    class_filter = "9º Ano D"
    
    current_class_students = df_students[df_students['class_name'] == class_filter]['student_id'].astype(str).str.replace('.0','').str.strip().unique().tolist()
    
    print(f"Lista Normalizada da Turma: {len(current_class_students)} alunos.")
    # assert len(current_class_students) == 30
    
    # 2. Preparar Dataframe de Notas (COM NORMALIZAÇÃO)
    df_final = df_assessments.copy()
    if not df_final.empty:
        df_final['student_id'] = df_final['student_id'].astype(str).str.replace('.0','').str.strip()
        
    # 3. PivotTable
    pivot_table = df_final.pivot_table(
        index='student_id', 
        columns='bncc_code', 
        values='level_numeric',
        aggfunc='mean'
    ).fillna(0)
    
    print(f"Linhas no Pivot (antes de reindex): {len(pivot_table)}")
    
    # 4. REINDEX (A CORREÇÃO)
    if current_class_students:
        pivot_table = pivot_table.reindex(current_class_students, fill_value=0)
        
    print(f"Linhas no Pivot (PÓS REINDEX): {len(pivot_table)}")
    
    # Validação Final
    if len(pivot_table) == 30:
        print("✅ SUCESSO: O Mapa de Calor exibiria 30 alunos devidamente.")
    else:
        print(f"❌ FALHA: O Mapa de Calor exibiria {len(pivot_table)} alunos.")
        missing = set(current_class_students) - set(pivot_table.index)
        print(f"Faltando: {missing}")

if __name__ == "__main__":
    test_heatmap_logic()
