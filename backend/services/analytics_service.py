import pandas as pd
from typing import List, Dict

def calcular_notas(df_assessments: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a situação atual de cada aluno por habilidade.
    Regra: Considera apenas o registro mais recente.
    Esta função foi migrada do Streamlit (app.py) original.
    """
    if df_assessments.empty:
        return pd.DataFrame()

    # Converter data para datetime para ordenação correta
    df_assessments['date'] = pd.to_datetime(df_assessments['date'], errors='coerce')
    
    # Ordenar por data decrescente (mais recente primeiro)
    df_sorted = df_assessments.sort_values(by='date', ascending=False)
    
    # 1. Manter apenas a última nota de CADA OBJETIVO (rubric_id)
    df_unique_obj = df_sorted.drop_duplicates(subset=['student_id', 'rubric_id'], keep='first')
    
    # 2. Agrupar por HABILIDADE (bncc_code) e calcular média
    df_unique_obj['level_assigned'] = pd.to_numeric(df_unique_obj['level_assigned'], errors='coerce')
    
    # Colunas de agrupamento
    group_cols = ['student_id', 'bncc_code']
    # Se existirem nome e turma, incluímos no agrupamento
    for col in ['class_name', 'student_name']:
        if col in df_unique_obj.columns:
            group_cols.append(col)
            
    df_final = df_unique_obj.groupby(group_cols)['level_assigned'].mean().reset_index()
    
    # Renomear para manter compatibilidade
    df_final.rename(columns={'level_assigned': 'level_numeric'}, inplace=True)
    
    # (Opcional) Traz de volta a data mais recente para referência
    df_dates = df_unique_obj.groupby(['student_id', 'bncc_code'])['date'].max().reset_index()
    df_final = df_final.merge(df_dates, on=['student_id', 'bncc_code'], how='left')

    return df_final

def converter_nivel_nota(nivel: float) -> float:
    """Converte nível (1-4) para nota (0-10)."""
    mapping = {1: 2.5, 2: 5.0, 3: 7.5, 4: 10.0}
    try:
        return mapping.get(int(nivel), 0.0)
    except:
        return 0.0
