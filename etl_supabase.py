import pandas as pd
from sqlalchemy import create_engine
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import os

with open("migration_log.txt", "w", encoding="utf-8") as f:
    f.write("=== INICIANDO MIGRACAO ETL DIRECT ===\n")

def log(msg):
    with open("migration_log.txt", "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

try:
    log("Iniciando conexão direta com Google Sheets...")
    
    # 1. Conexão via gspread usando a GCP Key existente
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('.streamlit/gcp_key.json', scope)
    client = gspread.authorize(creds)
    
    # URL Fornecida pelo Usuário
    sheet_url = "https://docs.google.com/spreadsheets/d/1Tlp2SQSsWMk2JcmvefiKbXFW0ATSe4UMMw2HIU5uSZA/edit?usp=sharing"
    sheet = client.open_by_url(sheet_url)
    log("Conexão e Autenticação com Google Sheets estabelecida com a conta de serviço (robo-escola).")

    # 2. Conexão PostgreSQL (Supabase)
    import urllib.parse
    password = urllib.parse.quote_plus("3ZreY/q6@V?i@a9")
    db_url = f"postgresql://postgres.zjsiznfbswlziuffyosi:{password}@aws-1-sa-east-1.pooler.supabase.com:5432/postgres"
    engine = create_engine(db_url)
    log("Conexão Supabase OK.")

    # 3. Mapeamento de abas
    tables = [
        "bncc_library"
    ]

    for table in tables:
        log(f"\n[{table}] Iniciando extração...")
        try:
            worksheet = sheet.worksheet(table)
            data = worksheet.get_all_records(expected_headers=[]) # [] = empty to auto detect
            df = pd.DataFrame(data)
            
            if df.empty:
                log(f"[{table}] Planilha vazia. Pulando...")
                continue
                
            # Limpeza
            df.columns = df.columns.str.strip().str.lower()
            df = df.dropna(how='all')
            
            # Tratativas Específicas
            if table == "users":
                if "must_change_password" in df.columns:
                    df["must_change_password"] = df["must_change_password"].apply(
                        lambda x: str(x).upper() in ['TRUE', '1', 'YES', 'S', 'VERDADEIRO']
                    )
                cols = [c for c in ['username', 'password', 'must_change_password'] if c in df.columns]
                df = df[cols]
                
            elif table == "setup_classes":
                if 'class_name' in df.columns:
                    df = df[['class_name']]
                
            elif table == "students":
                cols = ['student_id', 'student_name', 'class_name']
                df = df[[c for c in cols if c in df.columns]]
                if 'student_id' in df.columns:
                    df['student_id'] = df['student_id'].astype(str).str.strip()
                    df['student_id'] = df['student_id'].apply(lambda x: x[:-2] if x.endswith('.0') else x)
                if 'student_name' in df.columns:
                    df['student_name'] = df['student_name'].astype(str).str.strip()
                if 'class_name' in df.columns:
                    df['class_name'] = df['class_name'].astype(str).str.strip()

            elif table == "setup_disciplines":
                 if 'discipline_name' in df.columns:
                    df = df[['discipline_name']]
                
            elif table == "bncc_library":
                # Rename columns based on actual sheet headers
                rename_map = {'code': 'bncc_code', 'description': 'skill_description'}
                df = df.rename(columns=rename_map)
                
                cols = ['bncc_code', 'skill_description']
                df = df[[c for c in cols if c in df.columns]]
                # Garantir que nao venham linhas fantasmas sem codigo BNCC (Restricao NOT NULL)
                if 'bncc_code' in df.columns:
                    df['bncc_code'] = df['bncc_code'].astype(str).str.strip()
                    df = df[df['bncc_code'] != '']
                    df = df[df['bncc_code'] != 'nan']
                    df = df.dropna(subset=['bncc_code'])
                
            elif table == "teacher_rubrics":
                cols = ['rubric_id', 'bncc_code', 'objective', 'level_1_desc', 'level_2_desc', 'level_3_desc', 'level_4_desc']
                df = df[[c for c in cols if c in df.columns]]
                for col in df.columns:
                    df[col] = df[col].astype(str).str.strip()

            elif table == "assessments":
                cols = ['student_id', 'rubric_id', 'bncc_code', 'level_assigned', 'date']
                if 'level_numeric' in df.columns and 'level_assigned' not in df.columns:
                    df.rename(columns={'level_numeric': 'level_assigned'}, inplace=True)
                df = df[[c for c in cols if c in df.columns]]
                if 'student_id' in df.columns:
                    df['student_id'] = df['student_id'].astype(str).str.strip()
                    df['student_id'] = df['student_id'].apply(lambda x: x[:-2] if x.endswith('.0') else x)
                if 'level_assigned' in df.columns:
                    # Filtra vazio 
                    df['level_assigned'] = df['level_assigned'].replace('', pd.NA)
                    df = df.dropna(subset=['level_assigned'])
                    df['level_assigned'] = pd.to_numeric(df['level_assigned'], errors='coerce')
                    df['level_assigned'] = df['level_assigned'].fillna(0).astype(int)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date

            # Tratar colunas que deveriam ser int mas vieram com string (disciplina_id por ex)
            if 'discipline_id' in df.columns:
                 df['discipline_id'] = pd.to_numeric(df['discipline_id'], errors='coerce')

            log(f"[{table}] Inserindo {len(df)} linhas no Postgres...")
            
            # Checar se a tabela existe no modelo e usar to_sql apenas para append
            try:
                df.to_sql(table, engine, if_exists='append', index=False)
                log(f"[{table}] OK - Registros inseridos com sucesso.")
            except Exception as sql_e:
                log(f"[{table}] AVISO SQL: A tabela existe no script? -> {sql_e}")
            
        except gspread.exceptions.WorksheetNotFound:
            log(f"[{table}] AVISO: Aba não encontrada na Planilha do Google.")
        except Exception as e:
            import traceback
            log(f"[{table}] ERRO: {e}\n{traceback.format_exc()}")

    log("=== MIGRACAO FINALIZADA ===")
    
except Exception as e:
    import traceback
    log(f"ERRO CRITICO GERAL: {e}\n{traceback.format_exc()}")

log("Fechando script.")
os._exit(0)
