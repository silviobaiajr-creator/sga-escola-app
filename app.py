import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, date
import traceback
import os
import time

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==============================================================================
st.set_page_config(
    page_title="SGA-H | Sistema de Gestão de Aprendizagem por Habilidades",
    page_icon="🎓",
    layout="wide"
)

# Configuração Global da Sidebar
with st.sidebar:
    
    st.markdown("### 🤖 Configuração IA (Vertex AI)")
    st.info("✅ Usando conta de serviço (GCP)")
    
    # Verificação visual (Arquivo OU Secrets)
    key_path = ".streamlit/gcp_key.json"
    
    if os.path.exists(key_path):
        st.success("IA Ativa! 🧠 (Arquivo Local)")
    elif "gcp_service_account" in st.secrets:
        st.success("IA Ativa! 🧠 (Secrets Cloud)")
    else:
        st.error(f"⚠️ Chave não encontrada! (Procurei em: {key_path} e nos Secrets)")
       

# Estilo personalizado para mensagens de erro/sucesso e tabelas
st.markdown("""
    <style>
    .stAlert { margin-top: 1rem; }
    .main-header { font-size: 2.5rem; color: #1E88E5; font-weight: bold; }
    .sub-header { font-size: 1.5rem; color: #424242; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. INFRAESTRUTURA E CONEXÃO
# ==============================================================================

# Conexão com Google Sheets usando st.connection (cache_ttl=0 garante dados frescos)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Erro ao conectar com Google Sheets. Verifique se o arquivo .streamlit/secrets.toml está configurado corretamente.")
    st.error(f"Detalhes: {e}")
    st.stop()

# Definição das abas obrigatórias
REQUIRED_SHEETS = [
    "setup_classes", "users", "students", "bncc_library", 
    "teacher_rubrics", "assessments", "setup_disciplines"
]

# Função para carregar dados (com cache manual para performance se necessário, mas aqui usando direto)
@st.cache_data(ttl=60) # Cache de 60s para evitar recarregamento constante e resets de tela
def get_data(worksheet_name):
    """Carrega dados de uma aba específica."""
    try:
        # ttl=15 evita erro 429 (Quota Exceeded) do Google Sheets
        df = conn.read(worksheet=worksheet_name, ttl=15)
        return df
    except Exception as e:
        # Se a aba não existir, tenta criar (embora o correto seja o admin criar a planilha base)
        # Aqui vamos apenas retornar vazio ou erro amigável
        st.error(f"Erro ao ler aba '{worksheet_name}': {e}")
        # st.warning(f"Aba '{worksheet_name}' não encontrada ou vazia. Verifique a planilha.")
        # Retorna DataFrame vazio com colunas esperadas para evitar crash
        return pd.DataFrame()

# @st.cache_resource(ttl=3600*24) # REMOVIDO: Cache agressivo impedia detectar novas colunas
@st.cache_data(ttl=600) # Cache de dados simples (10 min) é suficiente
def get_static_data(worksheet_name):
    """Carrega dados estáticos (BNCC, Setup)."""
    try:
        # ttl alto também na chamada, mas o cache_resource que segura
        return conn.read(worksheet=worksheet_name, ttl=600)
    except Exception as e:
        st.error(f"Erro ao ler estático '{worksheet_name}': {e}")
        return pd.DataFrame()

def save_data(df, worksheet_name):
    """Salva/Sobrescreve dados em uma aba específica."""
    try:
        conn.update(worksheet=worksheet_name, data=df)
        st.cache_data.clear() # Limpar cache para garantir atualização imediata
        st.success(f"Dados salvos com sucesso em '{worksheet_name}'!")
    except Exception as e:
        st.error(f"Erro ao salvar em '{worksheet_name}': {e}")

# ==============================================================================
# 2. MODELAGEM DE DADOS E VALIDAÇÃO ESSENCIAL
# ==============================================================================

def validate_schema():
    """Verifica se as colunas essenciais existem para o funcionamento do sistema."""
    # Esta função poderia ser expandida para criar as abas se não existirem
    pass 

# ==============================================================================
# 3. AUTENTICAÇÃO
# ==============================================================================

# Funções auxiliares de sessão
import json
import os

SESSION_FILE = ".streamlit/session.json"

def save_session(user_info):
    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        with open(SESSION_FILE, "w") as f:
            json.dump(user_info, f)
    except Exception as e:
        print(f"Erro ao salvar sessão: {e}")

def load_session():
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar sessão: {e}")
    return None

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def login():
    """Sistema simples de login com persistência."""
    
    # 1. Tentar carregar sessão salva se não estiver logado
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        saved_user = load_session()
        if saved_user:
            st.session_state["logged_in"] = True
            st.session_state["user_info"] = saved_user
            # Não faz rerun aqui para evitar loop, o app segue o fluxo normal

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["user_info"] = None

    if not st.session_state["logged_in"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<h1 style='text-align: center;'>🔐 Login SGA-H</h1>", unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Usuário / CPF")
                password = st.text_input("Senha", type="password")
                submit_login = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit_login:
                # Usar connection direta com ttl=0 para garantir dados frescos e pegar mudanças de senha
                try:
                    users_df = conn.read(worksheet="users", ttl=0)
                except Exception as e:
                    st.error(f"Erro ao ler usuários: {e}")
                    return
                
                if users_df.empty:
                    st.error("Tabela de usuários não encontrada ou vazia.")
                    return

                # LIMPEZA DE COLUNAS (Remover espaços nos cabeçalhos)
                users_df.columns = users_df.columns.str.strip()

                # Verifica credenciais
                def clean_val(val):
                    val_str = str(val).strip()
                    if val_str.endswith('.0'):
                        return val_str[:-2]
                    return val_str

                users_df['username'] = users_df['username'].apply(clean_val)
                users_df['password'] = users_df['password'].apply(clean_val)
                
                user = users_df[
                    (users_df["username"] == clean_val(username)) & 
                    (users_df["password"] == clean_val(password))
                ]

                if not user.empty:
                    user_data = user.iloc[0].to_dict()
                    
                    # --- RECURSO: SENHA TEMPORÁRIA ---
                    # Verifica se coluna existe
                    force_reset = False
                    if 'must_change_password' in user_data:
                        raw_val = user_data['must_change_password']
                        # Tratamento robusto para Booleans e Strings
                        if isinstance(raw_val, bool) and raw_val:
                            force_reset = True
                        else:
                            val_reset = str(raw_val).strip().upper()
                            # Correção para Float (1.0 -> 1)
                            if val_reset.endswith('.0'):
                                val_reset = val_reset[:-2]
                                
                            if val_reset in ['TRUE', '1', 'YES', 'S', 'VERDADEIRO']:
                                force_reset = True
                            
                    if force_reset:
                        st.session_state["reset_mode"] = True
                        st.session_state["temp_user_info"] = user_data
                        st.rerun()
                    else:
                        st.session_state["logged_in"] = True
                        st.session_state["user_info"] = user_data
                        save_session(user_data) # Salva sessão no disco
                        st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
    # --- FLUXO DE TROCA DE SENHA (FORÇADO) ---
    if "reset_mode" in st.session_state and st.session_state["reset_mode"]:
         u_temp = st.session_state["temp_user_info"]
         
         col1, col2, col3 = st.columns([1, 2, 1])
         with col2:
             st.markdown("### ⚠️ Troca de Senha Obrigatória")
             st.info("Você está acessando com uma senha temporária. Defina sua nova senha abaixo.")
             
             with st.form("reset_pwd_form"):
                 new_pwd = st.text_input("Nova Senha", type="password")
                 confirm_pwd = st.text_input("Confirmar Nova Senha", type="password")
                 submit_reset = st.form_submit_button("Atualizar Senha", type="primary", use_container_width=True)
                 
             if submit_reset:
                 if new_pwd != confirm_pwd:
                     st.error("As senhas não coincidem.")
                 elif len(new_pwd) < 4:
                     st.error("A senha deve ter pelo menos 4 caracteres.")
                 else:
                     # Atualizar na Planilha
                     users_updated = conn.read(worksheet="users", ttl=0)
                     
                     # Limpeza robusta para garantir match do índice
                     # (Mesma lógica do login: remove .0 e strip)
                     def clean_val_reset(val):
                         val_str = str(val).strip()
                         if val_str.endswith('.0'): return val_str[:-2]
                         return val_str

                     users_updated['username_clean'] = users_updated['username'].apply(clean_val_reset)
                     
                     # DEBUG: Mostrar dados para entender o erro
                     st.write(f"DEBUG: Buscando usuário: '{str(u_temp['username'])}'")
                     st.write("DEBUG: Lista de usuários limpa:", users_updated[['username', 'username_clean']])

                     # Localizar Índice
                     idx = users_updated[users_updated['username_clean'] == str(u_temp['username'])].index
                     
                     if not idx.empty:
                         st.write(f"DEBUG: Usuário encontrado no índice: {idx}")
                         users_updated.loc[idx, 'password'] = new_pwd
                         users_updated.loc[idx, 'must_change_password'] = 'FALSE'
                         
                         # Remover coluna temporária antes de salvar
                         if 'username_clean' in users_updated.columns:
                             del users_updated['username_clean']

                         save_data(users_updated, "users")
                         st.success("Senha atualizada com sucesso! 🎉")
                         time.sleep(1.5)
                         
                         # Logar usuário
                         u_temp['password'] = new_pwd
                         u_temp['must_change_password'] = 'FALSE'
                         st.session_state["user_info"] = u_temp
                         st.session_state["logged_in"] = True
                         del st.session_state["reset_mode"]
                         del st.session_state["temp_user_info"]
                         save_session(u_temp)
                         st.rerun()
                     else:
                         st.error("Erro ao localizar usuário para atualização.")
         
         return False # Não deixa passar para o app principal ainda
    
    # Adicionar botão de logout na sidebar se estiver logado
    if st.session_state["logged_in"]:
        with st.sidebar:
            st.divider()
            # PDF Upload removido conforme solicitação (Uso exclusivo da Planilha)
            # with st.expander("⚙️ Config. BNCC (PDF)"): ...
            
            if st.button("Sair (Logout)"):
                st.session_state["logged_in"] = False
                st.session_state["user_info"] = None
                clear_session()
                st.rerun()

    return st.session_state["logged_in"]

# ==============================================================================
# 6. REGRA DE NEGÓCIO (CÁLCULO DE NOTAS)
# ==============================================================================

def calcular_notas(df_assessments):
    """
    Calcula a situação atual de cada aluno por habilidade.
    Regra: Considera apenas o registro mais recente.
    """
    if df_assessments.empty:
        return pd.DataFrame()

    # Converter data para datetime para ordenação correta
    # Assumindo formato YYYY-MM-DD ou DD/MM/YYYY, o pandas costuma inferir bem
    df_assessments['date'] = pd.to_datetime(df_assessments['date'], errors='coerce')
    
    # Ordenar por data decrescente (mais recente primeiro)
    df_sorted = df_assessments.sort_values(by='date', ascending=False)
    
    # 1. Manter apenas a última nota de CADA OBJETIVO (rubric_id)
    # Usuário pode ter avaliado o mesmo objetivo várias vezes, vale a última.
    df_unique_obj = df_sorted.drop_duplicates(subset=['student_id', 'rubric_id'], keep='first')
    
    # 2. Agrupar por HABILIDADE (bncc_code) e calcular média
    # level_assigned deve ser numérico
    df_unique_obj['level_assigned'] = pd.to_numeric(df_unique_obj['level_assigned'], errors='coerce')
    
    # Groupby devolve DataFrame com índice composto, reset_index traz de volta
    # Incluir Nome e Turma no agrupamento para não perder
    group_cols = ['class_name', 'student_id', 'student_name', 'bncc_code']
    # Garantir que colunas existem
    for col in group_cols:
        if col not in df_unique_obj.columns:
            df_unique_obj[col] = 'N/A'
            
    df_final = df_unique_obj.groupby(group_cols)['level_assigned'].mean().reset_index()
    
    # Renomear para manter compatibilidade, mas indicando que é média
    df_final.rename(columns={'level_assigned': 'level_numeric'}, inplace=True)
    
    # Se precisar de metadados da última avaliação (ex: data), podemos fazer merge ou pegar max
    # Mas para o heatmap o importante é o level_numeric.
    
    # (Opcional) Traz de volta a data mais recente para referência
    df_dates = df_unique_obj.groupby(['student_id', 'bncc_code'])['date'].max().reset_index()
    df_final = df_final.merge(df_dates, on=['student_id', 'bncc_code'], how='left')

    return df_final

def converter_nivel_nota(nivel):
    """Converte nível (1-4) para nota (0-10)."""
    mapping = {1: 2.5, 2: 5.0, 3: 7.5, 4: 10.0}
    try:
        return mapping.get(int(nivel), 0.0)
    except:
        return 0.0

# ==============================================================================
# 7. FUNÇÕES IA (SUB-CHEF)
# ==============================================================================

# --- CONFIGURAÇÃO AI (GCP VERTEX AI) ---
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account
import json
import os
import PyPDF2

import re

# Função para extrair texto do PDF (RAG Simples Melhorado)
def extract_text_from_pdf(pdf_path, search_term=None):
    """
    Lê o PDF e retorna o texto. 
    Se search_term for fornecido, tenta retornar apenas páginas relevantes (Case Insensitive + Regex).
    """
    text = ""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                # Se tiver termo de busca, filtra (Case Insensitive + Regex)
                if search_term:
                    # Normaliza para busca flexível
                    # Ex: "COMPETÊNCIAS ESPECÍFICAS" -> busca ignorando acentos ou case seria ideal, 
                    # mas startswith search_term raw regex
                    if re.search(search_term, page_text, re.IGNORECASE):
                        text += page_text + "\n---\n"
                else:
                    text += page_text + "\n"
        return text
        
        # Se filtro não retornou nada, retorna tudo (fallback) ou aviso
        if search_term and not text:
            return "" # Não encontrou o termo específico
            
        return text # RETORNAR TUDO (SEM LIMITE DE 30k) - Modelos Flash aguentam 1M+ tokens
    except Exception as e:
        print(f"Erro ao ler PDF: {e}")
        return ""

# Função para inicializar Vertex AI

# Função para inicializar Vertex AI
@st.cache_resource
def init_vertex_ai():
    """Inicializa o Vertex AI com a conta de serviço."""
    try:
        # 1. Tenta carregar do arquivo local (Dev)
        key_path = ".streamlit/gcp_key.json"
        if os.path.exists(key_path):
            credentials = service_account.Credentials.from_service_account_file(key_path)
            
        # 2. Se não tiver arquivo, tenta carregar dos Secrets (Prod/Cloud)
        elif "gcp_service_account" in st.secrets:
            # st.secrets retorna um AttrDict, precisamos converter para dict padrão se necessário
            service_account_info = st.secrets["gcp_service_account"]
            credentials = service_account.Credentials.from_service_account_info(service_account_info)
            
        else:
            return None, "Chave GCP não encontrada (Arquivo ou Secrets)."

        # Inicializa Vertex AI
        vertexai.init(project="escola-sga", location="us-central1", credentials=credentials)
        
        return True, "Vertex AI Conectado!"
    except Exception as e:
        return None, f"Erro ao conectar Vertex AI: {str(e)}"

# Lista de modelos para tentar (Fallback - Versões 2026)
CANDIDATE_MODELS = [
    "gemini-2.5-flash",       # Mais recente/rápido
    "gemini-2.0-flash-001",   # Versão anterior estável
    "gemini-2.5-pro",         # Mais robusto (se flash falhar)
    "gemini-1.5-flash-001"    # Legado (última tentativa)
]

def safe_generate_content(prompt):
    """Tenta gerar conteúdo usando vários modelos em sequência até um funcionar."""
    last_error = None
    
    for model_name in CANDIDATE_MODELS:
        try:
            model = GenerativeModel(model_name)
            # Tenta gerar
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            last_error = e
            # Se for erro 404 (Model not found) ou 429 (Quota), continua para o próximo
            print(f"Tentativa falhou com {model_name}: {e}")
            continue
            
    # Se todos falharem, levanta o último erro
    raise last_error

def generate_objectives(skill_code, skill_description, quantity=3, discipline_name=None):
    """
    Usa Vertex AI para gerar objetivos (com fallback e contexto PDF).
    """
    success, msg = init_vertex_ai()
    if not success:
        return [f"Erro: {msg}"], ""
    
    # 1. Tentar contexto da Planilha (bncc_competencies) - Fonte ÚNICA
    sheet_context = ""
    error_detail = ""
    try:
        df_comp = get_static_data("bncc_competencies")
        if not df_comp.empty and discipline_name:
            # Normalizar colunas
            df_comp.columns = df_comp.columns.str.strip().str.lower()
            if 'discipline' in df_comp.columns and 'competencies_text' in df_comp.columns:
                # Normaliza para busca (lower)
                target = str(discipline_name).strip().lower()
                # Tenta match exato na coluna disciplina
                row = df_comp[df_comp['discipline'].astype(str).str.strip().str.lower() == target]
                
                if not row.empty:
                    sheet_context = row.iloc[0]['competencies_text']
                else:
                    error_detail = f"(Não encontrado para '{target}'. IDs disponíveis: {df_comp['discipline'].unique()})"
            else:
                error_detail = "(Colunas 'discipline' ou 'competencies_text' não encontradas)"
        else:
             error_detail = "(Aba 'bncc_competencies' vazia ou não encontrada)"
    except Exception as e:
        error_detail = f"(Erro na leitura: {str(e)})"
        
    # SEM PDF - Apenas Planilha conforme solicitado
    
    # Montar Mensagem de Contexto Final
    final_context = ""
    if sheet_context:
        final_context += f"\n--- COMPETÊNCIAS ESPECÍFICAS (DA PLANILHA) ---\n{sheet_context}\n"
        
    context_msg = ""
    if final_context.strip():
        context_msg = f"\nCONTEXTO PEDAGÓGICO:\n{final_context}\nUse este contexto para alinhar os objetivos."

    prompt = f"""
    Atue como um Especialista Pedagógico (Sub-Chef) Sênior.
    
    1. ANALISE O CONTEXTO (Competências da Disciplina + Habilidade BNCC):
    Habilidade: {skill_code} - {skill_description}
    {context_msg}
    
    2. TAREFA - Gere DUAS saídas:
    
    [PARTE A] EXPLICAÇÃO PEDAGÓGICA (Breve):
    - Explique em 1 parágrafo como os objetivos cobrem toda a habilidade progressivamente (por que começou com o primeiro e terminou com o último).
    - Conecte com as Competências Específicas se houver contexto.
    - Se NÃO houver contexto de competências acima, explique com base no seu conhecimento geral da BNCC para a disciplina.
    
    [PARTE B] OBJETIVOS DE AULA (Lista):
    - Crie {quantity} objetivos práticos e diretos.
    - IMPORTANTE: Independentemente da quantidade ({quantity}), os objetivos devem cobrir a habilidade NA TOTALIDADE, de forma progressiva (do básico ao complexo).
    - O primeiro objetivo deve introduzir o tema e o último deve consolidar a habilidade completa.
    - NÃO use frases introdutórias. Comece direto com o verbo.
    - Use verbos da Taxonomia de Bloom adequados.
    - SEJA EXTREMAMENTE OBJETIVO. Frases curtas, diretas e práticas. 
    - EVITE: "O aluno deve...", "Ser capaz de...". USE: "Identificar...", "Calcular...", "Analisar...".
    - MÁXIMO 15 palavras por objetivo.
    
    FORMATO DE SAÍDA OBRIGATÓRIO (Use o separador "###" entre as partes):
    EXPLICAÇÃO: [Sua explicação aqui]
    ###
    OBJETIVO 1
    OBJETIVO 2
    OBJETIVO 3
    ...
    """
    
    try:
        text = safe_generate_content(prompt)
        
        # Parser da Resposta
        explanation = "Explicação não gerada."
        objectives_raw = ""
        
        if "###" in text:
            parts = text.split("###")
            explanation = parts[0].replace("EXPLICAÇÃO:", "").strip()
            objectives_raw = parts[1].strip()
        else:
            # Fallback se a IA esquecer o separador
            objectives_raw = text
            explanation = "A IA gerou os objetivos diretamente."

        # Processar Lista de Objetivos
        lines = []
        for line in objectives_raw.split('\n'):
            # Limpeza (remover marcadores, números, e linhas vazias)
            cleaned = line.strip().lstrip('-').lstrip('*').lstrip('1.').lstrip('2.').lstrip('3.').lstrip('4.').lstrip('5.').strip()
            
            # Filtro inteligente: Ignorar linhas que são apenas labels (ex: "OBJETIVO 1", "Objetivo 2:")
            is_label = re.match(r'^OBJETIVO\s*\d+[:.]*$', cleaned, re.IGNORECASE)
            
            if cleaned and not cleaned.endswith(':') and not is_label: 
                lines.append(cleaned)
        
        return lines[:quantity], f"📌 Contexto Utilizado:\n{explanation}\n\n📂 Fonte(s):\n{'✅ Planilha (Competências do ' + str(discipline_name) + ')' if sheet_context else '❌ Planilha (Não encontrado) ' + error_detail}"
        
    except Exception as e:
        return [f"Erro na IA (Vertex): {str(e)}"], ""

# ... (mantém generate_rubric inalterado)

# ... (código intermediário omitido, foca na atualização da TAB 1 e TAB 4)

# PARA ATUALIZAR TAB 1 (CHAMADA):
# Buscar nas linhas ~713 onde chama generate_objectives e passar discipline_name=selected_disc_name

# PARA ATUALIZAR TAB 4 (HEATMAP):
# Buscar linhas ~1250 onde define tab_g1

# (Como replace_file_content não suporta editar múltiplos locais distantes sem multi_replace,
#  vou focar primeiro na função generate_objectives e depois fazer outra chamada para Tab 1 e Tab 4)


def generate_rubric(skill_code, objective):
    """
    Usa Vertex AI para gerar rubrica (com fallback).
    """
    success, msg = init_vertex_ai()
    if not success:
        return {}
        
    prompt = f"""
    Atue como um Especialista em Avaliação.
    Objetivo da Aula: {objective}
    Habilidade Original: {skill_code}
    
    Tarefa: Crie uma régua de avaliação (rubrica) de 4 níveis para este objetivo específico.
    Nível 1 (Iniciante): O aluno tem dificuldades graves ou confunde conceitos básicos.
    Nível 2 (Básico): O aluno identifica conceitos mas não sabe aplicar ou justificar.
    Nível 3 (Proficiente - Meta): O aluno atinge o objetivo completamente.
    Nível 4 (Avançado): O aluno vai além, relacionando com outros contextos ou criando algo novo.
    
    Saída OBRIGATÓRIA: Formato texto puro:
    N1: Descrição...
    N2: Descrição...
    N3: Descrição...
    N4: Descrição...
    """
    
    try:
        text = safe_generate_content(prompt)
        
        rubric = {}
        for line in text.split('\n'):
            clean_line = line.strip()
            if clean_line.startswith("N1:"): rubric[1] = clean_line.replace("N1:", "").strip()
            elif clean_line.startswith("N2:"): rubric[2] = clean_line.replace("N2:", "").strip()
            elif clean_line.startswith("N3:"): rubric[3] = clean_line.replace("N3:", "").strip()
            elif clean_line.startswith("N4:"): rubric[4] = clean_line.replace("N4:", "").strip()
            
        return rubric
    except Exception as e:
        st.error(f"Erro Vertex AI: {e}")
        return {}

# ==============================================================================
# MÓDULOS DO SISTEMA
# ==============================================================================

def admin_module():
    st.title("🛠️ Painel do Administrador")
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload de Alunos", "📊 Dashboards Analíticos", "📚 Upload Habilidades"])
    
    # --- ABA 1: GESTÃO DE ALUNOS ---
    with tab1:
        st.subheader("Cadastro de Alunos")
        
        tipo_cadastro = st.radio("Selecione o método:", ["📂 Upload via CSV", "✍️ Cadastro Manual"], horizontal=True)

        # ---------------------------------------------------------
        # OPÇÃO A: CADASTRO MANUAL NOVO
        # ---------------------------------------------------------
        if tipo_cadastro == "✍️ Cadastro Manual":
            with st.form("form_aluno_manual"):
                st.markdown("### Novo Aluno")
                
                # Carregar turmas para o seletor
                setup_df = get_static_data("setup_classes")
                if setup_df.empty:
                    st.error("Configure as turmas em setup_classes primeiro!")
                    turmas_ops = []
                else:
                    turmas_ops = setup_df["class_name"].unique().tolist()
                
                c1, c2 = st.columns(2)
                with c1:
                    m_nome = st.text_input("Nome Completo")
                with c2:
                    m_id = st.text_input("Matrícula (ID Único)")
                
                m_turma = st.selectbox("Turma", options=turmas_ops)

                # Checkbox para permitir atualização
                update_existing = st.checkbox("Atualizar dados se a matrícula já existir?")
                
                submitted_manual = st.form_submit_button("Salvar Aluno")
                
                if submitted_manual:
                    if not m_nome or not m_id or not m_turma:
                        st.error("Preencha todos os campos!")
                    else:
                        current_students = get_data("students")
                        
                        # Função de limpeza de ID (mesma lógica da senha para evitar erro 1000.0 != 1000)
                        def clean_id(val):
                            val_str = str(val).strip()
                            if val_str.endswith('.0'):
                                return val_str[:-2]
                            return val_str

                        # Preparar ID de entrada
                        input_id_clean = clean_id(m_id)
                        
                        # Verificar duplicidade
                        if not current_students.empty:
                             # Criar coluna limpa temporária para comparação
                             current_students['id_clean'] = current_students['student_id'].apply(clean_id)
                             existing_ids = set(current_students['id_clean'])
                        else:
                             existing_ids = set()
                        
                        if input_id_clean in existing_ids:
                            if update_existing:
                                # Lógica de Atualização (Sobrescrever)
                                # Encontrar o índice da linha que tem esse ID
                                idx_to_update = current_students.index[current_students['id_clean'] == input_id_clean].tolist()
                                
                                # Atualizar dados (nome e turma)
                                for idx in idx_to_update:
                                    current_students.at[idx, 'student_name'] = m_nome.strip()
                                    current_students.at[idx, 'class_name'] = m_turma
                                
                                # Remover coluna temp antes de salvar
                                if 'id_clean' in current_students.columns:
                                    current_students = current_students.drop(columns=['id_clean'])
                                    
                                save_data(current_students, "students")
                                st.success(f"Cadastro do aluno {m_nome} (ID {input_id_clean}) ATUALIZADO com sucesso!")
                            else:
                                # Bloquear
                                st.error(f"⛔ A matrícula '{input_id_clean}' JÁ EXISTE! Marque a caixa 'Atualizar dados...' se deseja sobrescrever.")
                        else:
                            # Tudo certo, salvar novo
                            new_student = pd.DataFrame([{
                                "student_id": input_id_clean, # Salvar o ID limpo
                                "student_name": m_nome.strip(),
                                "class_name": m_turma
                            }])
                            
                            # Remover coluna temp se existir no current antes do concat
                            if 'id_clean' in current_students.columns:
                                current_students = current_students.drop(columns=['id_clean'])

                            updated_students = pd.concat([current_students, new_student], ignore_index=True)
                            save_data(updated_students, "students")
                            st.success(f"Aluno {m_nome} cadastrado com sucesso na turma {m_turma}!")

        # ---------------------------------------------------------
        # OPÇÃO B: UPLOAD CSV (LÓGICA EXISTENTE)
        # ---------------------------------------------------------
        elif tipo_cadastro == "📂 Upload via CSV":
            st.info("O CSV deve conter as colunas: student_id, student_name, class_name")
            
            uploaded_file = st.file_uploader("Carregar arquivo CSV", type=["csv"])
            
            if uploaded_file:
                try:
                    df_upload = pd.read_csv(uploaded_file)
                    
                    # Validação de Colunas
                    required_cols = {'student_id', 'student_name', 'class_name'}
                    if not required_cols.issubset(df_upload.columns):
                        st.error(f"O CSV deve conter as colunas: {required_cols}")
                    else:
                        # 3.A. VALIDAÇÃO CRUZADA COM setup_classes
                        setup_df = get_static_data("setup_classes")
                        if setup_df.empty:
                            st.error("Aba 'setup_classes' está vazia! Configure as turmas antes de importar alunos.")
                        else:
                            valid_classes = set(setup_df["class_name"].unique())
                            uploaded_classes = set(df_upload["class_name"].unique())
                            
                            invalid_classes = uploaded_classes - valid_classes
                            
                            if invalid_classes:
                                st.error(f"❌ Upload Bloqueado! Turmas não cadastradas encontradas: {invalid_classes}")
                                st.warning(f"Turmas permitidas (conforme setup_classes): {sorted(list(valid_classes))}")
                            else:
                                st.success("✅ Validação de turmas aprovada!")
                                st.dataframe(df_upload.head())
                                
                                if st.button("Confirmar Importação"):
                                    # Lógica para adicionar (Append) sem duplicar matrículas seria ideal,
                                    # mas o requisito pede Append/Salvar. Vamos carregar o atual e concatenar.
                                    current_students = get_data("students")
                                    
                                    # Evitar duplicidade de matrícula (regra extra de integridade)
                                    if not current_students.empty:
                                        existing_ids = set(current_students['student_id'].astype(str))
                                        new_ids = set(df_upload['student_id'].astype(str))
                                        
                                        overlap = existing_ids.intersection(new_ids)
                                        if overlap:
                                            st.warning(f"Atenção: {len(overlap)} matrículas já existem e serão duplicadas se prosseguir. Considere limpar antes.")
                                    
                                    # Concatenar
                                    updated_students = pd.concat([current_students, df_upload], ignore_index=True)
                                    save_data(updated_students, "students")
                
                except Exception as e:
                    st.error(f"Erro ao processar CSV: {e}")

    # --- ABA 2: DASHBOARDS ANALÍTICOS (Renomeado de tab3) ---
    with tab2:
        st.subheader("Visão Geral da Escola")
        
        assessments_df = get_data("assessments")
        if assessments_df.empty:
            st.info("Ainda não há avaliações registradas.")
        else:
            # Aplicar Regra de Negócio: Calcular situação atual
            df_atual = calcular_notas(assessments_df)
            
            # Conversão para Nota Numérica (Média * 2.5)
            # level_assigned foi renomeado para level_numeric em calcular_notas
            df_atual['Nota'] = df_atual['level_numeric'] * 2.5
            
            st.markdown("### 📈 Conversão de Níveis em Notas (0-10)")
            st.dataframe(df_atual[['class_name', 'student_id', 'bncc_code', 'level_numeric', 'Nota']])
            
            # Alerta de Risco
            st.markdown("### 🚨 Alerta de Risco Pedagógico")
            # Filtrar alunos com Nível < 2 (Média)
            risk_df = df_atual[df_atual['level_numeric'] < 2.0]
            
            # Contar quantas habilidades com nível 1 cada aluno tem
            risk_count = risk_df.groupby(['class_name', 'student_id']).size().reset_index(name='count_level_1')
            
            # Filtrar quem tem mais de 3
            high_risk = risk_count[risk_count['count_level_1'] > 3]
            
            if high_risk.empty:
                st.success("Nenhum aluno em situação de alto risco (> 3 habilidades no nível 1).")
            else:
                st.error(f"Atenção: {len(high_risk)} alunos com dificuldades críticas.")
                st.dataframe(high_risk)

    # --- ABA 3: UPLOAD BNCC (NOVO) ---
    with tab3:
        st.subheader("📚 Biblioteca de Habilidades (BNCC)")
        
        with st.expander("📂 Instruções para Upload", expanded=True):
            st.markdown("""
            **Formato do CSV:**
            - Colunas obrigatórias: `code`, `description`, `discipline`
            - `code`: Código da habilidade (ex: EF01MA01)
            - `description`: Texto completo
            - `discipline`: Sigla da disciplina (ex: MAT, PORT, CIE)
            """)
            
        bncc_file = st.file_uploader("Carregar Habilidades (CSV)", type=["csv"], key="bncc_upload")
        
        if bncc_file:
            try:
                # Tentar ler com separadores comuns
                try:
                    df_bncc_up = pd.read_csv(bncc_file, sep=',', encoding='utf-8')
                    if len(df_bncc_up.columns) < 2:
                         bncc_file.seek(0)
                         df_bncc_up = pd.read_csv(bncc_file, sep=';', encoding='utf-8')
                except:
                    bncc_file.seek(0)
                    df_bncc_up = pd.read_csv(bncc_file, sep=';', encoding='latin1')
                
                # Normalizar colunas
                df_bncc_up.columns = df_bncc_up.columns.str.strip().str.lower()
                
                required = {'code', 'description'}
                if not required.issubset(df_bncc_up.columns):
                     st.error(f"Colunas obrigatórias faltando: {required}")
                else:
                     st.dataframe(df_bncc_up.head())
                     
                     if st.button("📥 Importar para Biblioteca"):
                         current_bncc = get_data("bncc_library")
                         
                         # Garantir disciplina
                         if 'discipline' not in df_bncc_up.columns:
                             df_bncc_up['discipline'] = 'GERAL'
                         else:
                             df_bncc_up['discipline'] = df_bncc_up['discipline'].astype(str).str.upper().str.strip()
                             
                         # Concatenar
                         if not current_bncc.empty:
                             # Remover duplicatas de código que estão vindo no upload
                             # (opcional: ou atualizar descriptions)
                             # Aqui: Append simples
                             final_bncc = pd.concat([current_bncc, df_bncc_up], ignore_index=True)
                         else:
                             final_bncc = df_bncc_up
                             
                         # Remover duplicatas exatas de código?
                         final_bncc.drop_duplicates(subset=['code'], keep='last', inplace=True)
                         
                         save_data(final_bncc, "bncc_library")
                         st.success("Biblioteca atualizada com sucesso!")
                         
            except Exception as e:
                st.error(f"Erro no processamento: {e}")


def get_discipline_quorum(discipline_code):
    """Retorna o número total de professores que lecionam a disciplina."""
    users = get_data("users")
    if users.empty: return 1
    count = 0
    if 'disciplina' in users.columns:
        code_norm = str(discipline_code).strip().upper()
        def check(val):
            if not val: return False
            discs = [d.strip().upper() for d in str(val).split(',')]
            return code_norm in discs
        count = users['disciplina'].apply(check).sum()
    return max(1, count)

def teacher_module(user_info):
    # 3. Layout Otimizado: Header compacto
    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown(f"### 🍎 Professor: **{user_info['name']}**")
    with c_head2:
        if st.button("Sair", key="logout_btn_top"):
            st.session_state["logged_in"] = False
    # --- DADOS GERAIS DO PROFESSOR (Escopo Global do Módulo) ---
    allowed_classes = [c.strip() for c in str(user_info.get('allowed_classes', '')).split(',')]
    
    # Carregar rubricas existentes (para uso global no módulo)
    current_rubrics = get_data("teacher_rubrics")
    
    # --- SUBSTITUIÇÃO DE ABAS POR MENU DE RÁDIO (CORREÇÃO DE RESETS) ---
    # `st.tabs` reinicia quando o script roda se não tivermos controle. O radio é mais robusto.
    # Menu horizontal simulando abas.
    
    tabs_options = ["📝 Planejamento", "✅ Avaliação", "📖 Biblioteca", "📊 Relatórios"]
    if "active_tab_teacher" not in st.session_state:
        st.session_state["active_tab_teacher"] = "📝 Planejamento"
        
    # Callback para mudar aba
    def change_tab():
        pass # O estado muda automaticamente pelo key do widget

    selected_tab = st.radio("Navegação:", tabs_options, horizontal=True, label_visibility="collapsed", key="active_tab_teacher", on_change=change_tab)
    st.divider()

    # Mapeamento do conteúdo das abas
    if selected_tab == "📝 Planejamento":
        tab_context = "tab1"
    elif selected_tab == "✅ Avaliação":
        tab_context = "tab2"
    elif selected_tab == "📖 Biblioteca":
        tab_context = "tab3"
    elif selected_tab == "📊 Relatórios":
        tab_context = "tab4"
    else:
        tab_context = "tab5"
    
    # --- ABA 1: PLANEJAMENTO ---
    if tab_context == "tab1":
        bncc_df = get_static_data("bncc_library")
        if bncc_df.empty:
            st.warning("Biblioteca BNCC vazia.")
        else:
            # 1. Seletor de Disciplina (USANDO IDs e NOMES - Corrigido Case Insensitive)
            # Carregar tabela de disciplinas para mapear ID -> Nome
            setup_discs = get_data("setup_disciplines")
            dict_disc_names = {} # Map ID_UPPER -> Nome
            if not setup_discs.empty:
                # Normaliza para maiúsculo para garantir match
                setup_discs['discipline_id'] = setup_discs['discipline_id'].astype(str).str.strip().str.upper()
                setup_discs['discipline_name'] = setup_discs['discipline_name'].astype(str).str.strip()
                dict_disc_names = dict(zip(setup_discs['discipline_id'], setup_discs['discipline_name']))

            # Pega string de IDs de disciplinas do usuário
            raw_ids = str(user_info.get('disciplina', '')).split(',')
            # Normaliza input do usuário também
            user_allowed_ids = [d.strip().upper() for d in raw_ids if d.strip()]
            
            if not user_allowed_ids:
                user_allowed_ids = ["GERAL"]
            
            # Criar lista de opções para o Selectbox (Nome Bonito)
            options_map = {}
            for uid in user_allowed_ids:
                # Busca no dict (pelo ID Upper). Se não achar, usa o próprio ID
                name = dict_disc_names.get(uid, uid) 
                options_map[name] = uid # Nome -> ID_UPPER
            
            selected_disc_name = st.selectbox("Selecione a Disciplina", list(options_map.keys()), key="plan_disc_sel")
            selected_discipline_id = options_map[selected_disc_name] # ID REAL

            
            # 2. Filtrar BNCC pela Disciplina (Usando ID)
            # Garantir coluna discipline
            if 'discipline' not in bncc_df.columns:
                bncc_df['discipline'] = 'Geral'
            
            # Filtrar pelo ID (Normalizar Base BNCC tb)
            bncc_df['discipline_norm'] = bncc_df['discipline'].astype(str).str.strip().str.upper()
            
            # --- FILTRO POR SÉRIE/ANO (v3.28) ---
            # Carregar turmas para identificar Séries Disponíveis
            # --- FILTRO POR SÉRIE/ANO (v3.28 - CORRIGIDO v3.51) ---
            # Carregar turmas para identificar Séries Disponíveis DA ESCOLA
            setup_classes = get_static_data("setup_classes")
            
            # Mapear Turmas -> Séries
            map_class_grade_plan = {}
            if not setup_classes.empty and 'grade' in setup_classes.columns:
                setup_classes['class_name'] = setup_classes['class_name'].astype(str).str.strip()
                setup_classes['grade'] = setup_classes['grade'].astype(str).str.strip()
                map_class_grade_plan = dict(zip(setup_classes['class_name'], setup_classes['grade']))

            # Identificar quais séries o professor tem acesso (IGUAL TAB 2)
            my_grades_plan = set()
            for t in allowed_classes:
                g = map_class_grade_plan.get(t, None)
                if g: my_grades_plan.add(g)
            
            # Se o professor não tiver nenhuma turma mapeada, fallback para mostrar tudo (evita bloqueio total)
            if not my_grades_plan:
                if not setup_classes.empty and 'grade' in setup_classes.columns:
                    available_grades = sorted(setup_classes['grade'].dropna().unique().tolist())
                else:
                    available_grades = ["Todos (Planilha sem coluna 'grade')"]
            else:
                available_grades = sorted(list(my_grades_plan))
                
            c_fil1, c_fil2 = st.columns([1, 3])
            with c_fil1:
                selected_grade = st.selectbox("Série/Ano", available_grades, key="plan_grade_sel")
            
            with c_fil2:
                # Filtrar BNCC (Disciplina + Série)
                bncc_filtered = bncc_df[bncc_df['discipline_norm'] == selected_discipline_id]
                
                # Se 'grade' existir na BNCC e o usuário selecionou algo válido
                if 'grade' in bncc_df.columns and selected_grade != "Todos (Planilha sem coluna 'grade')":
                    # FIX (v3.31): Garantir que não haja colunas duplicadas que causem erro no .str
                    bncc_df = bncc_df.loc[:, ~bncc_df.columns.duplicated()]
                    
                    # Normalizar para evitar "6 ano" != "6º Ano"
                    bncc_df['grade_norm'] = bncc_df['grade'].astype(str).str.strip().str.lower()
                    sel_grade_norm = str(selected_grade).strip().lower()
                    bncc_filtered = bncc_filtered[bncc_df['grade_norm'] == sel_grade_norm]
                
                selected_code = None # Inicializar para evitar UnboundLocalError se a lista for vazia
                if bncc_filtered.empty:
                    st.info(f"Nenhuma habilidade para {selected_disc_name} no {selected_grade}.")
                    st.session_state["selected_skill_code"] = None # Reset
                else:
                    # --- NOVO SELETOR DE HABILIDADES (Inteligente) ---
                    if "selected_skill_code" not in st.session_state:
                        st.session_state["selected_skill_code"] = None
                    
                    # Se já tiver um selecionado, mostra qual é e botão de alterar
                    if st.session_state["selected_skill_code"]:
                        sel_code = st.session_state["selected_skill_code"]
                        # Busca descrição
                        desc_sel = bncc_filtered[bncc_filtered['code'] == sel_code]['description'].values[0] if not bncc_filtered[bncc_filtered['code'] == sel_code].empty else ""
                        
                        c_sel1, c_sel2 = st.columns([4, 1])
                        with c_sel1:
                            st.info(f"**Habilidade Selecionada:** {sel_code}")
                            st.caption(desc_sel)
                        with c_sel2:
                            if st.button("🔄 Alterar", key="btn_change_skill"):
                                st.session_state["selected_skill_code"] = None
                                st.rerun()
                        selected_code = sel_code
                    else:
                        # Seletor Expandido
                        with st.expander("🔍 Selecionar Habilidade (Clique para abrir)", expanded=True):
                            st.markdown("##### Habilidades Disponíveis:")
                            for idx, row in bncc_filtered.iterrows():
                                with st.container(border=True):
                                    c_skill1, c_skill2 = st.columns([5, 1])
                                    with c_skill1:
                                        st.markdown(f"**{row['code']}**")
                                        st.caption(row['description'])
                                    with c_skill2:
                                        if st.button("Selecionar", key=f"btn_sel_{row['code']}"):
                                            st.session_state["selected_skill_code"] = row['code']
                                            st.rerun()
                        selected_code = None
            
            # Só avança se tiver código
            if selected_code:
                # 7. Exibir Descrição Completa (Já mostrada acima, mas mantemos fluxo)
                full_desc = bncc_filtered[bncc_filtered['code'] == selected_code]['description'].values[0]
                
                
                # --- [RESTO DA LÓGICA MANTIDA] ---
                # ... (Código ignorado pela substituição até o próximo bloco) ...
                



                # --- 🔍 VERIFICAÇÃO DE STATUS (FLAG SYSTEM) ---
                is_approved = False
                is_pending = False
                has_drafts = False
                draft_objs = []
                
                # Vamos buscar direto da fonte
                all_rubs = get_data("teacher_rubrics")
                
                if not all_rubs.empty:
                    if 'status' not in all_rubs.columns: all_rubs['status'] = 'APPROVED'
                    if 'discipline_id' not in all_rubs.columns: all_rubs['discipline_id'] = 'GERAL'
                    if 'bncc_code' not in all_rubs.columns: all_rubs['bncc_code'] = ''
                    
                    curr_disc = selected_discipline_id
                    
                    # 1. Check APPROVED
                    mask_approved = (
                        (all_rubs['bncc_code'] == selected_code) & 
                        (all_rubs['discipline_id'] == curr_disc) &
                        (all_rubs['status'] == 'APPROVED')
                    )
                    if not all_rubs[mask_approved].empty:
                        is_approved = True
                    
                    # 2. Check PENDING (Restaurado)
                    mask_pending = (
                        (all_rubs['bncc_code'] == selected_code) & 
                        (all_rubs['discipline_id'] == curr_disc) &
                        (all_rubs['status'] == 'PENDING')
                    )
                    if not all_rubs[mask_pending].empty:
                            is_pending = True
                    
                    # 3. Check DRAFTS (Agora roda SEMPRE, independente de estar aprovado ou não)
                    # Normalizar status para busca correta
                    all_rubs['status'] = all_rubs['status'].astype(str).str.strip().str.upper() 
                    
                    mask_draft = (
                        (all_rubs['bncc_code'] == selected_code) & 
                        (
                            (all_rubs['status'] == 'DRAFT') | 
                            # FIX (v3.37): PENDING só é rascunho se a régua estiver VAZIA.
                            # Se já tiver conteúdo em desc_level_1, é uma PROPOSTA AGUARDANDO, não um rascunho de IA.
                            (
                                (all_rubs['status'] == 'PENDING') & 
                                (all_rubs['teacher_username'] == user_info['username']) &
                                (all_rubs['desc_level_1'].fillna('').astype(str).str.strip() == '')
                            )
                        )
                    )
                    drafts_df = all_rubs[mask_draft]
                    
                    if not drafts_df.empty:
                        # Filtro extra: Objetivo não pode ser vazio
                        drafts_df = drafts_df[drafts_df['objective'].astype(str).str.strip() != '']
                        
                        if not drafts_df.empty:
                            has_drafts = True
                            draft_objs = drafts_df['objective'].unique().tolist()
                
                # ATUALIZAR STATUS LEGADO (Para compatibilidade com checks abaixo)
                skill_status = "NOT_STARTED" # Default para evitar UnboundLocalError
                if is_approved: skill_status = "APPROVED"
                elif is_pending: skill_status = "PENDING"
                elif has_drafts: skill_status = "DRAFT"
                
                st.markdown("---")

                # CASO 1: APROVADO (Lógica v3.27 Restaurada + Fix Rascunhos)
                if is_approved:
                    if not has_drafts:
                        st.success("🔒 **Habilidade Já Aprovada**")
                        st.write("Esta habilidade já possui objetivos definidos e padronizados pela escola.")
                        st.info("👉 Verifique a aba **'📖 Biblioteca'**.")
                        return 
                    else:
                         st.info("🔓 **Habilidade Aprovada (Com Rascunhos Pendentes)**: Você pode finalizar os rascunhos abaixo.") 

                # CASO 2: PENDING (Bloqueio Parcial - Exceção para Rascunhos)
                if is_pending:
                    st.warning("🗳️ **Habilidade em Votação**")
                    st.write("Existe uma proposta aguardando aprovação.")
                    
                    if not has_drafts:
                        st.info("Visualização apenas (Aguarde a votação).")
                        return # Se não tiver rascunho, bloqueia tudo
                    else:
                        st.info("🔓 **Desbloqueio Parcial:** Existem rascunhos pendentes encontrados. Você pode transformá-los em réguas.")

                # CASO 3: DRAFT (Apenas Aviso)
                if has_drafts and not is_pending:
                    st.warning("⚠️ Existem rascunhos para esta habilidade.")

                # RENDERIZAÇÃO DE RASCUNHOS (Se houver)
                if has_drafts:
                    st.markdown("### 📝 Retomar Rascunho (Converter em Régua)")
                    if draft_objs:
                        radio_key_draft = f"radio_draft_{selected_code}"
                        selected_draft = st.radio("Selecione o Rascunho:", draft_objs, key=radio_key_draft)
                        
                        # Sync
                        if f"last_{radio_key_draft}" not in st.session_state:
                            st.session_state[f"last_{radio_key_draft}"] = None
                        
                        if st.session_state[f"last_{radio_key_draft}"] != selected_draft:
                            # CRITICAL FIX: Update the TEXT AREA key directly to force re-render
                            st.session_state[f"area_draft_{selected_code}"] = selected_draft
                            # Update auxiliary key as well
                            st.session_state[f"edit_obj_{selected_code}"] = selected_draft
                            st.session_state[f"last_{radio_key_draft}"] = selected_draft

                        # CAMPO DE EDIÇÃO (Restaurado)
                        current_draft_edit = st.session_state.get(f"edit_obj_{selected_code}", selected_draft)
                        
                        # CORREÇÃO WARNING (v3.50): Não passar 'value' se a key já estiver no session_state
                        txt_key = f"area_draft_{selected_code}"
                        txt_kwargs = {"label": "Editar Objetivo (Rascunho):", "height": 100, "key": txt_key}
                        if txt_key not in st.session_state:
                            txt_kwargs["value"] = current_draft_edit
                            
                        final_draft_text = st.text_area(**txt_kwargs)
                        
                        # Sync reverso (Text Area -> Session)
                        if final_draft_text != current_draft_edit:
                             st.session_state[f"edit_obj_{selected_code}"] = final_draft_text

                        if st.button("📏 Gerar Régua para este Rascunho", key="btn_resume_draft"):
                             # Guardar ID original REAL (vindo do DF)
                             # Isso garante que se o rascunho for de OUTRO professor, a gente apague a linha certa
                             origin_row = drafts_df[drafts_df['objective'] == selected_draft]
                             if not origin_row.empty:
                                 origin_id = origin_row['rubric_id'].values[0]
                                 st.session_state[f"origin_draft_id_{selected_code}"] = origin_id
                             else:
                                 # Fallback (improvável com a lógica atual)
                                 import re
                                 safe_origin = re.sub(r'[^a-zA-Z0-9]', '', selected_draft)[:20]
                                 st.session_state[f"origin_draft_id_{selected_code}"] = f"{user_info['username']}_{selected_code}_{safe_origin}"

                             with st.spinner("Gerando..."):
                                 rub = generate_rubric(str(selected_code), str(final_draft_text))
                                 if rub:
                                    st.session_state[f"rub_{selected_code}"] = rub
                                    st.session_state[f"edit_obj_{selected_code}"] = final_draft_text
                                    st.success("Régua gerada! Revise abaixo.")

                # FORCE STOP se estiver PENDING (para não renderizar IA em baixo)
                if is_pending:
                    st.write("---") 
                    st.caption("🚫 Geração de novos objetivos bloqueada durante votação.")
                    # Pular o resto do bloco de IA
                    if f"rub_{selected_code}" in st.session_state:
                         # Se gerou régua acima, renderiza form
                         pass
                    else:
                         return # Encerra aqui se não retomou rascunho

                use_ai = False
                if not has_drafts and not is_pending:
                    st.markdown("### 👨‍🍳 O Sub-Chef (IA)")
                    use_ai = st.toggle("Ativar Assistente de Planejamento", value=True)
                
                ai_rubric_fill = {} 
                
                if use_ai:
                    quant_slider = st.slider("Quantidade de Sugestões:", 1, 5, 3)
                    
                    if st.button("🔪 Fatiar Habilidade (Gerar Objetivos de Aula)"):
                        with st.spinner("O Sub-Chef está fatiando a habilidade..."):
                            # Passar ID da disciplina para match correto na planilha (ex: MAT, HIST)
                            if 'selected_discipline_id' in locals():
                                disc_param = selected_discipline_id
                            else:
                                disc_param = selected_disc_name # Fallback
                                
                            objectives, used_context = generate_objectives(selected_code, full_desc, quantity=quant_slider, discipline_name=disc_param)
                            st.session_state[f"objs_{selected_code}"] = objectives
                            st.session_state[f"ctx_{selected_code}"] = used_context

                            # --- PERSISTÊNCIA IMEDIATA (DRAFT) ---
                            new_drafts = []
                            import re
                            current_rubs_local = get_data("teacher_rubrics")
                            
                            for obj in objectives:
                                safe_obj = re.sub(r'[^a-zA-Z0-9]', '', obj)[:20]
                                unique_id = f"{user_info['username']}_{selected_code}_{safe_obj}"
                                
                                new_drafts.append({
                                    "rubric_id": unique_id,
                                    "teacher_username": user_info['username'],
                                    "bncc_code": selected_code,
                                    "objective": obj,
                                    "status": "DRAFT", 
                                    "discipline_id": disc_param,
                                    "approvals": ""
                                })
                            
                            if new_drafts:
                                df_drafts = pd.DataFrame(new_drafts)
                                # Garantir colunas
                                for col in df_drafts.columns:
                                    if col not in current_rubs_local.columns:
                                        current_rubs_local[col] = ""
                                
                                df_updated_drafts = pd.concat([current_rubs_local, df_drafts], ignore_index=True)
                                save_data(df_updated_drafts, "teacher_rubrics")
                                st.toast("Objetivos salvos como Rascunho! 💾")
                                time.sleep(1) 
                                st.rerun()
                
                # Se já tiver objetivos gerados para essa habilidade (E NÃO FOR RASCUNHO PENDENTE)
                # Se for Rascunho, o bloco "Retomar" acima já cuidou disso. Evitar duplicidade.
                if f"objs_{selected_code}" in st.session_state and skill_status != "DRAFT":
                    # Exibir contexto debug se existir
                    if f"ctx_{selected_code}" in st.session_state and st.session_state[f"ctx_{selected_code}"]:
                        with st.expander("🧠 Explicação Pedagógica & Contexto"):
                            st.markdown(st.session_state[f"ctx_{selected_code}"])
                    
                    # Cardápio
                    st.markdown("**Escolha um Objetivo de Aula (Cardápio):**")
                    obj_options = st.session_state[f"objs_{selected_code}"]
                         
                    if obj_options and isinstance(obj_options, list):
                        # Sincronização Radio -> Text Area
                        radio_key = f"radio_{selected_code}"
                        text_key = f"edit_obj_{selected_code}"
                        
                        # 1. Radio (com key)
                        selected_obj_raw = st.radio("Objetivos Sugeridos:", obj_options, label_visibility="collapsed", key=radio_key)

                        # 2. Verifica se mudou
                        if f"last_{radio_key}" not in st.session_state:
                            st.session_state[f"last_{radio_key}"] = selected_obj_raw
                        
                        if st.session_state[f"last_{radio_key}"] != selected_obj_raw:
                            # Mudou! Atualiza o text area
                            st.session_state[text_key] = selected_obj_raw
                            st.session_state[f"last_{radio_key}"] = selected_obj_raw

                        st.caption("📝 *Você pode editar o objetivo abaixo antes de criar a régua:*")
                        
                        # 3. Text Area (com key vinculada)
                        selected_obj = st.text_area("Objetivo Selecionado:", key=text_key, height=70)

                        if st.button("📏 Criar Régua (Gerar Rubrica)"):
                            with st.spinner(f"Criando régua para: {selected_obj}..."):
                                rubric_gen = generate_rubric(str(selected_code), str(selected_obj))
                                if rubric_gen:
                                    st.session_state[f"rub_{selected_code}"] = rubric_gen
                                    st.success("Régua pronta! Veja abaixo 👇")
                    else:
                        st.error("Erro no formato dos objetivos.")
                
                # Recuperar rubrica gerada se existir
                if f"rub_{selected_code}" in st.session_state:
                    ai_rubric_fill = st.session_state[f"rub_{selected_code}"]

                # --- FIM IA ---

                with st.form("rubric_form"):
                    if skill_status == "APPROVED":
                         st.warning("Visualização Apenas (Somente Leitura - Aprovado pela Escola)")

                    st.markdown(f"**Defina os critérios para: {selected_code}**")
                    
                    # Usa o valor da sessão (que a IA pode ter preenchido ou o usuário editado)
                    current_obj_val = st.session_state.get(f"edit_obj_{selected_code}", "")
                    final_objective = st.text_input("Objetivo da Aula (Opcional/IA)", value=current_obj_val)

                    c_rub1, c_rub2 = st.columns(2)
                    with c_rub1:
                        # Se tiver AI, usa o valor dela, senão vazio
                        val_l1 = ai_rubric_fill.get(1, "")
                        val_l2 = ai_rubric_fill.get(2, "")
                        
                        l1 = st.text_area("Nível 1 (Iniciante)", value=val_l1, height=100)
                        l2 = st.text_area("Nível 2 (Básico)", value=val_l2, height=100)
                    with c_rub2:
                        val_l3 = ai_rubric_fill.get(3, "")
                        val_l4 = ai_rubric_fill.get(4, "")
                        
                        l3 = st.text_area("Nível 3 (Proficiente)", value=val_l3, height=100)
                        l4 = st.text_area("Nível 4 (Avançado)", value=val_l4, height=100)
                    
                    submitted = st.form_submit_button("Salvar Rubrica")
                    if submitted:
                        # Criar ID único
                        import re
                        safe_obj = re.sub(r'[^a-zA-Z0-9]', '', final_objective)[:20]
                        unique_rubric_id = f"{user_info['username']}_{selected_code}_{safe_obj}"

                        # LÓGICA DE APROVAÇÃO COLABORATIVA
                        current_disc_id = selected_discipline_id
                        if current_disc_id == 'GERAL': current_disc_id = 'GERAL' # Fallback
                        
                        quorum = get_discipline_quorum(current_disc_id)
                        approvals_list = [user_info['username']]
                        
                        # Se quórum for 1 (só eu), já aprova. Senão PENDING.
                        status_final = "PENDING"
                        if len(approvals_list) >= quorum:
                            status_final = "APPROVED"
                            msg_success = f"Régua aprovada e publicada! (Quórum: {quorum})"
                        else:
                            msg_success = f"Proposta enviada! Aguardando aprovação dos pares ({len(approvals_list)}/{quorum} votos)."

                        new_rubric = pd.DataFrame([{
                            "rubric_id": unique_rubric_id,
                            "teacher_username": user_info['username'],
                            "bncc_code": selected_code,
                            "objective": final_objective,
                            "desc_level_1": l1,
                            "desc_level_2": l2,
                            "desc_level_3": l3,
                            "desc_level_4": l4,
                            "status": status_final,
                            "approvals": ",".join(approvals_list),
                            "discipline_id": current_disc_id
                        }])
                        
                        # Garantir colunas novas no DataFrame principal se não existirem
                        cols_order = ["rubric_id", "teacher_username", "bncc_code", "objective", "desc_level_1", "desc_level_2", "desc_level_3", "desc_level_4", "status", "approvals", "discipline_id"]
                        
                        for col in cols_order:
                            if col not in current_rubrics.columns:
                                current_rubrics[col] = ""
                                
                        updated_rubrics = pd.concat([current_rubrics, new_rubric], ignore_index=True)
                        
                        # Manter colunas extras se existirem (created_at etc)
                        final_cols = [c for c in updated_rubrics.columns if c in cols_order or c not in new_rubric.columns]
                        updated_rubrics = updated_rubrics[final_cols]

                        # Remove duplicatas pelo ID DA RUBRICA
                        updated_rubrics.drop_duplicates(subset=['rubric_id'], keep='last', inplace=True)
                        
                        # Limpar rascunho órfão se houver (caso texto tenha sido editado mudando o ID)
                        if f"origin_draft_id_{selected_code}" in st.session_state:
                            origin_id = st.session_state[f"origin_draft_id_{selected_code}"]
                            if origin_id != unique_rubric_id:
                                updated_rubrics = updated_rubrics[updated_rubrics['rubric_id'] != origin_id]
                            # Limpar trigger
                            del st.session_state[f"origin_draft_id_{selected_code}"]
                        
                        save_data(updated_rubrics, "teacher_rubrics")
                        
                        # LIMPEZA DE CAMPOS (Novo Requisito)
                        keys_to_clear = [f"edit_obj_{selected_code}", f"rub_{selected_code}", f"objs_{selected_code}", f"ctx_{selected_code}"]
                        for k in keys_to_clear:
                            if k in st.session_state:
                                del st.session_state[k]

                        st.success(msg_success)
                        time.sleep(1) # Dar tempo de ler a msg
                        st.rerun()

    # --- ABA 2: AVALIAÇÃO CONTÍNUA ---
    # --- ABA 2: AVALIAÇÃO CONTÍNUA (Refatorado 11/02) ---
    # --- ABA 2: AVALIAÇÃO CONTÍNUA (Refatorado 11/02) ---
    if tab_context == "tab2":
        # 0. PREPARAR DADOS DE SÉRIE/TURMA (Hierarquia v3.40)
        setup_classes = get_static_data("setup_classes")
        
        # Mapa: Turma -> Série
        map_class_grade = {}
        if not setup_classes.empty and 'grade' in setup_classes.columns:
            # Normalizar para garantir match
            setup_classes['class_name'] = setup_classes['class_name'].astype(str).str.strip()
            setup_classes['grade'] = setup_classes['grade'].astype(str).str.strip()
            map_class_grade = dict(zip(setup_classes['class_name'], setup_classes['grade']))
        
        # Identificar quais séries o professor tem acesso
        # authorized_classes vem de user_info['allowed_classes']
        my_grades = set()
        for t in allowed_classes:
            g = map_class_grade.get(t, "N/I") # N/I = Não Identificado/Cadastrado
            my_grades.add(g)
        
        sorted_grades = sorted(list(my_grades))

        # 1. BARRA DE CONTROLE SUPERIOR (Data, Bimestre, SÉRIE, Turma)
        c_top1, c_top2, c_top3, c_top4 = st.columns([1, 1, 1.5, 1.5])
        
        with c_top1:
            data_ref = st.date_input("📅 Data", datetime.now(), format="DD/MM/YYYY")
        with c_top2:
            bimester = st.selectbox("📌 Bimestre", ["1º", "2º", "3º", "4º"])
        
        with c_top3:
            # SELETOR DE SÉRIE (Novo v3.40)
            selected_grade_ref = st.selectbox("🎓 Série/Ano", sorted_grades)
        
        with c_top4:
            # SELETOR DE TURMA (Filtrado pela Série)
            # Apenas turmas que são desta série E que o professor pode ver
            filtered_classes = [c for c in allowed_classes if map_class_grade.get(c, "N/I") == selected_grade_ref]
            
            if not filtered_classes:
                filtered_classes = allowed_classes # Fallback se não bater nada
                
            selected_class = st.selectbox("🏫 Turma", filtered_classes)

        st.divider()

        # 2. SELETORES HIERÁRQUICOS (Disciplina -> Habilidade -> Objetivo)
        # Carregar Rubricas do Professor
        rubrics_df = get_data("teacher_rubrics")
        if not rubrics_df.empty:
            rubrics_df.columns = rubrics_df.columns.str.strip()
        
        # A. Disciplina
        # ... Lógica de mapeamento de nomes ...
        setup_discs = get_static_data("setup_disciplines")
        dict_disc_names = {}
        if not setup_discs.empty:
            setup_discs['discipline_id'] = setup_discs['discipline_id'].astype(str).str.strip().str.upper()
            setup_discs['discipline_name'] = setup_discs['discipline_name'].astype(str).str.strip()
            dict_disc_names = dict(zip(setup_discs['discipline_id'], setup_discs['discipline_name']))

        raw_ids = str(user_info.get('disciplina', '')).split(',')
        user_allowed_ids = [d.strip().upper() for d in raw_ids if d.strip()]
        if not user_allowed_ids: user_allowed_ids = ["GERAL"]
        
        options_map = {dict_disc_names.get(uid, uid): uid for uid in user_allowed_ids}
        
        c_sel1, c_sel2 = st.columns([1, 2])
        with c_sel1:
            selected_disc_name = st.selectbox("📚 Disciplina", list(options_map.keys()), key="assess_disc_sel")
            selected_discipline_id = options_map[selected_disc_name]

        # Filtra rubricas da disciplina E SÉRIE
        if not rubrics_df.empty:
             # Merge com BNCC para garantir filtro por disciplina E GRADE
             bncc_ref = get_static_data("bncc_library")
             if not bncc_ref.empty:
                 bncc_ref['code'] = bncc_ref['code'].astype(str).str.strip()
                 # Garantir colunas únicas na BNCC antes do merge
                 bncc_ref = bncc_ref.loc[:, ~bncc_ref.columns.duplicated()]
                 
                 rubrics_df['bncc_code'] = rubrics_df['bncc_code'].astype(str).str.strip()
                 
                 # CORREÇÃO v3.51: Merge também da COLUNA 'grade'
                 cols_to_merge = ['code', 'discipline']
                 if 'grade' in bncc_ref.columns:
                     cols_to_merge.append('grade')
                 
                 rubrics_df = rubrics_df.merge(bncc_ref[cols_to_merge], left_on='bncc_code', right_on='code', how='left')
                 
                 # 1. Filtro Disciplina
                 if 'discipline' in rubrics_df.columns:
                     rubrics_df['discipline_norm'] = rubrics_df['discipline'].astype(str).str.strip().str.upper()
                     filtered_rubrics = rubrics_df[rubrics_df['discipline_norm'] == selected_discipline_id]
                 else:
                     filtered_rubrics = rubrics_df # Fallback
                 
                 # 2. Filtro Série (CRÍTICO v3.51)
                 # Se a rubrica tiver 'grade' vinda da BNCC, filtra pelo seletor de topo
                 if 'grade' in filtered_rubrics.columns:
                     # Normalizar ambos
                     filtered_rubrics['grade_norm'] = filtered_rubrics['grade'].astype(str).str.strip().str.lower()
                     target_grade_norm = str(selected_grade_ref).strip().lower()
                     
                     filtered_rubrics = filtered_rubrics[filtered_rubrics['grade_norm'] == target_grade_norm]
             else:
                 filtered_rubrics = rubrics_df
             
             # --- FILTRO DE APROVAÇÃO (CRÍTICO) ---
             # Só permite avaliar objetivos APROVADOS
             if not filtered_rubrics.empty and 'status' in filtered_rubrics.columns:
                 filtered_rubrics = filtered_rubrics[filtered_rubrics['status'] == 'APPROVED']
             
        else:
            filtered_rubrics = pd.DataFrame()

        # B. Habilidade (Unique Codes)
        with c_sel2:
            if filtered_rubrics.empty:
                st.warning("Nenhuma rubrica encontrada para esta disciplina.")
                selected_skill = None
                selected_rubric_row = None
            else:
                # Selectbox Habilidade
                unique_skills = filtered_rubrics['bncc_code'].unique()
                selected_skill = st.selectbox("🎯 Habilidade (BNCC)", unique_skills, key="assess_unique_skill")
                
                # Selectbox Objetivo (Filtrado pela Habilidade)
                objs_for_skill = filtered_rubrics[filtered_rubrics['bncc_code'] == selected_skill]
                
                # Mapa reverso para ID
                # Exibe: "Objetivo..."
                obj_options = objs_for_skill['objective'].tolist()
                selected_obj_text = st.selectbox("📝 Objetivo Específico", obj_options, key="assess_obj_sel")
                
                # Recuperar row completa
                selected_rubric_row = objs_for_skill[objs_for_skill['objective'] == selected_obj_text].iloc[0]

        # 3. TABELA DE LANÇAMENTO (Data Editor)
        if selected_skill and selected_rubric_row is not None:
             st.info(f"Avaliando: **{selected_skill}** | {selected_obj_text}")
             
             # --- RÉGUA DE AVALIAÇÃO (Mobile Friendly) ---
             # Expander fechado por padrão para economizar espaço
             with st.expander("📖 Ver Critérios de Avaliação (Régua)", expanded=False):
                 st.markdown(f"""
                 **N1 (1.0 - 2.9):**
                 {selected_rubric_row.get('desc_level_1', 'Não definido')}
                 
                 **N2 (3.0 - 5.9):**
                 {selected_rubric_row.get('desc_level_2', 'Não definido')}
                 
                 **N3 (6.0 - 7.9):**
                 {selected_rubric_row.get('desc_level_3', 'Não definido')}
                 
                 **N4 (8.0 - 10.0):**
                 {selected_rubric_row.get('desc_level_4', 'Não definido')}
                 """)
             
             students_df = get_data("students")
             if not students_df.empty:
                class_students = students_df[students_df['class_name'] == selected_class].copy()
                
                if not class_students.empty:
                    # Preparar DataFrame para Edição
                    editor_df = class_students[['student_id', 'student_name']].copy()
                    
                    # --- LÓGICA DE DETECÇÃO DE DUPLICIDADE ---
                    # Buscar avaliações existentes para esta turma/disciplina/habilidade
                    # Idealmente filtraria por data ou bimestre também, mas o alerta geral é útil
                    existing_assessments = get_data("assessments")
                    
                    # Dicionário de notas existentes: student_id -> Nível
                    existing_map = {}
                    
                    if not existing_assessments.empty:
                        # Filtros de contexto
                        # Garante colunas
                        if 'rubric_id' not in existing_assessments.columns: existing_assessments['rubric_id'] = None
                        
                        mask = (
                            (existing_assessments['class_name'] == selected_class) &
                            (existing_assessments['rubric_id'] == selected_rubric_row['rubric_id']) &
                            (existing_assessments['bimester_ref'] == bimester) # Alerta por bimestre faz sentido
                        )
                        filtered_history = existing_assessments[mask]
                        
                        # Criar mapa (última nota lançada)
                        for _, row in filtered_history.iterrows():
                            existing_map[row['student_id']] = row['level_assigned']

                    # Adicionar coluna de Status/Alerta
                    def get_status(sid):
                        if sid in existing_map:
                            return f"⚠️ Nota: {int(existing_map[sid])}"
                        return ""
                    
                    def get_default_level(sid):
                         if sid in existing_map:
                             return str(int(existing_map[sid]))
                         return None

                    editor_df['Status'] = editor_df['student_id'].apply(get_status)
                    
                    # Pré-preencher nível? O usuário pediu apenas AVISO.
                    # Mas se quiser editar/corrigir, seria bom ver.
                    # Vamos deixar o campo Nível vazio para forçar nova entrada consciente, ou mostrar o aviso.
                    # Decisão: Manter Nível vazio para novo lançamento, Status avisa do anterior.
                    
                    editor_df['Nível'] = None 
                    editor_df['Nível'] = editor_df['Nível'].astype(str)

                    # Configuração da Coluna
                    edited_df = st.data_editor(
                        editor_df,
                        column_config={
                            "student_id": st.column_config.TextColumn("ID", disabled=True),
                            "student_name": st.column_config.TextColumn("Nome Sem Espaço", width="medium", disabled=True), 
                            "Status": st.column_config.TextColumn(
                                "Histórico (Bimestre)", 
                                disabled=True,
                                help="Mostra se o aluno já tem nota neste objetivo neste bimestre"
                            ),
                            "Nível": st.column_config.SelectboxColumn(
                                "Nível (1-4)",
                                help="Selecione o nível alcançado",
                                width="small",
                                options=["1", "2", "3", "4"],
                                required=False
                            )
                        },
                        hide_index=True,
                        use_container_width=True,
                        key="grades_editor"
                    )
                    
                    if st.button("💾 Salvar Avaliações", type="primary", use_container_width=True):
                         new_assessments = []
                         timestamp = datetime.now().isoformat()
                         count = 0
                         
                         for index, row in edited_df.iterrows():
                             nivel = row['Nível']
                             # Só salva se tiver nível selecionado E (importante) ignorar o None/Nan
                             if nivel and str(nivel).strip() in ['1','2','3','4']: 
                                 new_assessments.append({
                                    "timestamp": timestamp,
                                    "date": data_ref,
                                    "bimester_ref": bimester,
                                    "grade_ref": selected_grade_ref, # (Novo v3.40 - Persistência de Série)
                                    "teacher": user_info['username'],
                                    "discipline": selected_discipline_id,
                                    "class_name": selected_class,
                                    "student_id": row['student_id'],
                                    "bncc_code": selected_skill,
                                    "rubric_id": selected_rubric_row['rubric_id'],
                                    "level_assigned": int(nivel)
                                })
                                 count += 1
                         
                         if count > 0:
                            df_new = pd.DataFrame(new_assessments)
                            current_assessments = get_data("assessments")
                            
                            if not current_assessments.empty:
                                if 'discipline' not in current_assessments.columns: current_assessments['discipline'] = 'Geral'
                                if 'rubric_id' not in current_assessments.columns: current_assessments['rubric_id'] = None
                                if 'grade_ref' not in current_assessments.columns: current_assessments['grade_ref'] = 'N/I' # Backfill visual
                            
                            df_updated = pd.concat([current_assessments, df_new], ignore_index=True)
                            save_data(df_updated, "assessments")
                            st.balloons()
                            st.success(f"{count} notas lançadas com sucesso!")
                         else:
                             st.warning("Nenhum nível selecionado para salvar.")

                else:
                    st.warning("Nenhum aluno encontrado nesta turma.")

    # --- ABA 3: BIBLIOTECA (Minhas Rubricas + Votação) ---
    if tab_context == "tab3":
        st.subheader("📚 Biblioteca & Colaboração")
        
        # Carregar dados atualizados
        full_library = get_data("teacher_rubrics")
        
        # Garantir colunas novas
        if not full_library.empty:
            if 'status' not in full_library.columns: full_library['status'] = 'APPROVED'
            if 'approvals' not in full_library.columns: full_library['approvals'] = ''
            if 'discipline_id' not in full_library.columns: full_library['discipline_id'] = 'GERAL'
            
            # Tratar nulos
            full_library['status'] = full_library['status'].fillna('APPROVED') # Legado é aprovado
            full_library['approvals'] = full_library['approvals'].fillna('')

        # --- SUB-ABAS (Novo Layout v3.39) ---
        t3_vote, t3_view = st.tabs(["🗳️ Votação & Aprovação", "📚 Visualizar Acervo"])

        # --- ABA 3.1: VOTAÇÃO (Lógica Existente) ---
        with t3_vote:
            st.markdown("### 🗳️ Propostas Pendentes de Aprovação")
            
            # Filtros para Votação:
            # User deve ver propostas DE SUAS DISCIPLINAS que estejam PENDING
            
            # Identificar disciplinas do usuário atual
            raw_ids_u = str(user_info.get('disciplina', '')).split(',')
            my_disciplines = [d.strip().upper() for d in raw_ids_u if d.strip()]
            if not my_disciplines: my_disciplines = ["GERAL"]
            
            if not full_library.empty:
                # Filtrar PENDING e Minhas Disciplinas
                pending_df = full_library[
                    (full_library['status'] == 'PENDING') & 
                    (full_library['discipline_id'].isin(my_disciplines))
                ].copy()
                
                if pending_df.empty:
                    st.info("Nenhuma proposta pendente para suas disciplinas.")
                else:
                    for idx, row in pending_df.iterrows():
                        with st.container(border=True):
                            c_vote1, c_vote2 = st.columns([3, 1])
                            with c_vote1:
                                st.markdown(f"**Disciplina:** {row['discipline_id']} | **Habilidade:** {row['bncc_code']}")
                                st.markdown(f"*{row['objective']}*")
                                st.caption(f"Autor: {row['teacher_username']}")
                            
                            with c_vote2:
                                current_approvals = str(row['approvals']).split(',')
                                current_approvals = [u.strip() for u in current_approvals if u.strip()]
                                
                                quorum_req = get_discipline_quorum(row['discipline_id'])
                                
                                st.markdown(f"**Votos: {len(current_approvals)}/{quorum_req}**")
                                
                                if user_info['username'] in current_approvals:
                                    st.success("✅ Seu voto já foi registrado.")
                                    st.caption("Aguardando demais professores.")
                            
                            # LOGICA MOVIDA PARA FORA DAS COLUNAS (Full Width)
                            if user_info['username'] not in current_approvals:
                                # Preparar Comparação (Diff) - Lógica "Smart Match" (v3.26)
                                # Problema: IDs mudam ao editar, então não dá pra filtrar por ID.
                                # Solução: Buscar histórico da mesma BNCC e encontrar o texto mais parecido.
                                
                                history_candidates = full_library[
                                    (full_library['bncc_code'] == row['bncc_code']) & 
                                    (full_library['discipline_id'] == row['discipline_id']) & 
                                    (full_library['status'] == 'HISTORY')
                                ]
                                
                                last_history = None
                                if not history_candidates.empty:
                                    import difflib
                                    # Encontrar o candidato mais similar (para evitar pegar histórico do Objetivo B ao ver o A)
                                    current_text = str(row['objective'])
                                    best_score = 0.0
                                    best_match = None
                                    
                                    for idx_h, h_row in history_candidates.iterrows():
                                        hist_text = str(h_row['objective'])
                                        score = difflib.SequenceMatcher(None, current_text, hist_text).ratio()
                                        # Priorizar o mais recente se houver empate? O iterrows preserva a ordem?
                                        # Se iteramos, vamos guardando o melhor.
                                        if score > best_score:
                                            best_score = score
                                            best_match = h_row
                                    
                                    # Threshold de similaridade (Ex: 0.4)
                                    # Se for < 40% parecido, provavelmente é outro objetivo da mesma habilidade.
                                    if best_score > 0.4:
                                        last_history = best_match

                                # Helper de Diff
                                import difflib
                                import html
                                import re
                                
                                def highlight_diff(text_old, text_new):
                                    if not text_old: text_old = ""
                                    if not text_new: text_new = ""
                                    
                                    # 1. Normalização de Texto (Crucial para evitar falso positivo)
                                    text_old = str(text_old).replace('\r', '').replace('\xa0', ' ')
                                    text_new = str(text_new).replace('\r', '').replace('\xa0', ' ')

                                    def tokenize(text):
                                        # Split por espaço, mas preservando o delimitador para reconstrução
                                        return re.split(r'(\s+)', text)

                                    words_old = tokenize(text_old)
                                    words_new = tokenize(text_new)
                                    
                                    d = difflib.SequenceMatcher(None, words_old, words_new)
                                    result = []
                                    
                                    for opcode, a0, a1, b0, b1 in d.get_opcodes():
                                        if opcode == 'equal':
                                            chunk = "".join(words_old[a0:a1])
                                            result.append(html.escape(chunk))
                                        elif opcode == 'insert':
                                            chunk = "".join(words_new[b0:b1])
                                            if chunk.strip():
                                                result.append(f"<span style='background-color: #d1e7dd; color: #0f5132; border-radius: 3px; font-weight: bold;'>{html.escape(chunk)}</span>")
                                            else:
                                                result.append(html.escape(chunk))
                                        elif opcode == 'delete':
                                            chunk = "".join(words_old[a0:a1])
                                            if chunk.strip():
                                                result.append(f"<span style='background-color: #f8d7da; color: #842029; text-decoration: line-through; border-radius: 3px;'>{html.escape(chunk)}</span>")
                                        elif opcode == 'replace':
                                            chunk_old = "".join(words_old[a0:a1])
                                            chunk_new = "".join(words_new[b0:b1])
                                            
                                            if chunk_old.strip():
                                                result.append(f"<span style='background-color: #f8d7da; color: #842029; text-decoration: line-through; border-radius: 3px; font-size: 0.9em; opacity: 0.8;'>{html.escape(chunk_old)}</span> ")
                                            
                                            if chunk_new.strip():
                                                # GREEN -> Padrão visual limpo e aprovado
                                                result.append(f"<span style='background-color: #d1e7dd; color: #0f5132; border-radius: 3px; font-weight: bold;'>{html.escape(chunk_new)}</span>")
                                            else:
                                                result.append(html.escape(chunk_new))
                                    
                                    return "".join(result).replace("\n", "<br>")

                                # --- MODO DE REVISÃO E EDIÇÃO UNIFICADO (v3.24) ---
                                st.markdown("##### 📝 Analisar & Validar Proposta")
                                st.caption("Revise os campos abaixo. Alterações em relação ao histórico aparecem destacadas acima.")

                                # >>>> BLOCO OBJETIVO (Diff + Edit)
                                if last_history is not None:
                                    old_obj = last_history['objective']
                                    if old_obj != row['objective']:
                                        # Só mostra diff se houver mudança real após normalização
                                        if str(old_obj).strip() != str(row['objective']).strip():
                                            st.markdown(f"👀 **Alteração no Objetivo:** {highlight_diff(old_obj, row['objective'])}", unsafe_allow_html=True)
                                
                                new_obj = st.text_area("Objetivo", value=row['objective'], key=f"p_obj_{row['rubric_id']}", height=70)
                                
                                # >>>> BLOCO NÍVEIS (Diff + Edit)
                                pc1, pc2 = st.columns(2)
                                with pc1:
                                    # Nível 1
                                    if last_history is not None:
                                        old_l1 = last_history.get('desc_level_1', '')
                                        if str(old_l1).strip() != str(row.get('desc_level_1', '')).strip():
                                            st.markdown(f"👀 **Alteração N1:** {highlight_diff(old_l1, row.get('desc_level_1', ''))}", unsafe_allow_html=True)
                                    nl1 = st.text_area("Nível 1", value=row.get('desc_level_1', ''), key=f"p_l1_{row['rubric_id']}", height=100)

                                    # Nível 2
                                    if last_history is not None:
                                        old_l2 = last_history.get('desc_level_2', '')
                                        if str(old_l2).strip() != str(row.get('desc_level_2', '')).strip():
                                            st.markdown(f"👀 **Alteração N2:** {highlight_diff(old_l2, row.get('desc_level_2', ''))}", unsafe_allow_html=True)
                                    nl2 = st.text_area("Nível 2", value=row.get('desc_level_2', ''), key=f"p_l2_{row['rubric_id']}", height=100)

                                with pc2:
                                    # Nível 3
                                    if last_history is not None:
                                        old_l3 = last_history.get('desc_level_3', '')
                                        if str(old_l3).strip() != str(row.get('desc_level_3', '')).strip():
                                            st.markdown(f"👀 **Alteração N3:** {highlight_diff(old_l3, row.get('desc_level_3', ''))}", unsafe_allow_html=True)
                                    nl3 = st.text_area("Nível 3", value=row.get('desc_level_3', ''), key=f"p_l3_{row['rubric_id']}", height=100)

                                    # Nível 4
                                    if last_history is not None:
                                        old_l4 = last_history.get('desc_level_4', '')
                                        if str(old_l4).strip() != str(row.get('desc_level_4', '')).strip():
                                            st.markdown(f"👀 **Alteração N4:** {highlight_diff(old_l4, row.get('desc_level_4', ''))}", unsafe_allow_html=True)
                                    nl4 = st.text_area("Nível 4", value=row.get('desc_level_4', ''), key=f"p_l4_{row['rubric_id']}", height=100)

                                # >>>> BOTÃO DE AÇÃO
                                if st.button("✅ Confirmar Aprovação (+ Salvar Edição)", key=f"vote_{row['rubric_id']}", type="primary"):
                                    # 0. Detectar Mudanças (Segurança de Voto)
                                    original_obj = row['objective']
                                    original_l1 = row.get('desc_level_1', '')
                                    original_l2 = row.get('desc_level_2', '')
                                    original_l3 = row.get('desc_level_3', '')
                                    original_l4 = row.get('desc_level_4', '')
                                    
                                    has_changes = (
                                        new_obj != original_obj or 
                                        nl1 != original_l1 or 
                                        nl2 != original_l2 or 
                                        nl3 != original_l3 or 
                                        nl4 != original_l4
                                    )

                                    # 1. & 2. Computar Voto (Com Histórico se houver mudança)
                                    if has_changes:
                                        # A. ARQUIVAR A VERSÃO ANTIGA (SEM ALTERAR TEXTO)
                                        full_library.at[idx, 'status'] = 'HISTORY' 
                                        
                                        # B. CRIAR NOVA VERSÃO (PENDING) com o TEXTO NOVO
                                        import time as tm
                                        ts_suffix = str(int(tm.time()))[-4:] # Suffix curto
                                        new_rubric_id = f"{user_info['username']}_{row['bncc_code']}_{ts_suffix}"
                                        
                                        new_version_row = pd.DataFrame([{
                                            "rubric_id": new_rubric_id,
                                            "teacher_username": user_info['username'], # Novo autor (quem editou)
                                            "bncc_code": row['bncc_code'],
                                            "objective": new_obj, # TEXTO NOVO
                                            "desc_level_1": nl1,
                                            "desc_level_2": nl2,
                                            "desc_level_3": nl3,
                                            "desc_level_4": nl4,
                                            "status": 'PENDING',
                                            "approvals": user_info['username'], # Reinicia votos
                                            "discipline_id": row['discipline_id']
                                        }])
                                        
                                        # Garantir colunas no novo DF
                                        for col in full_library.columns:
                                            if col not in new_version_row.columns:
                                                    new_version_row[col] = "" # Preencher vazios
                                        
                                        full_library = pd.concat([full_library, new_version_row], ignore_index=True)
                                        msg_vote = "⚠️ Edição detectada! Versão anterior arquivada (Histórico) e nova votação iniciada."
                                        new_status = 'PENDING'

                                    else:
                                        # SEM MUDANÇA: Atualiza (inócuo) e adiciona voto
                                        full_library.at[idx, 'objective'] = new_obj
                                        full_library.at[idx, 'desc_level_1'] = nl1
                                        full_library.at[idx, 'desc_level_2'] = nl2
                                        full_library.at[idx, 'desc_level_3'] = nl3
                                        full_library.at[idx, 'desc_level_4'] = nl4
                                        
                                        new_list = current_approvals + [user_info['username']]
                                        msg_vote = "Voto computado com sucesso! 👍"
                                        
                                        # Verificar Quórum
                                        new_status = 'PENDING'
                                        if len(new_list) >= quorum_req:
                                            new_status = 'APPROVED'
                                        
                                        full_library.at[idx, 'approvals'] = ",".join(new_list)
                                        full_library.at[idx, 'status'] = new_status
                                    
                                    # 4. Salvar
                                    save_data(full_library, "teacher_rubrics")
                                    
                                    if new_status == 'APPROVED':
                                        st.balloons()
                                        st.success(f"{msg_vote} Régua Aprovada e Publicada Oficialmente! 🎉")
                                    else:
                                        st.warning(msg_vote) if has_changes else st.success(msg_vote)
                                    
                                    time.sleep(2.5) 
                                    st.rerun()

        # --- ABA 3.2: VISUALIZAR ACERVO (Nova Funcionalidade) ---
        with t3_view:
            st.markdown("### 📚 Acervo de Habilidades & Objetivos")
            
            # Filtros
            c_filter1, c_filter2 = st.columns(2)
            with c_filter1:
                # Identificar disciplinas do usuário atual (reuso)
                all_my_discs = ["Todas"] + my_disciplines
                sel_disc_view = st.selectbox("Filtrar por Disciplina:", all_my_discs, key="view_filter_disc")
            
            with c_filter2:
                sel_status_view = st.multiselect(
                    "Filtrar por Status:", 
                    ["APPROVED", "PENDING"], 
                    default=["APPROVED", "PENDING"],
                    key="view_filter_status"
                )
            
            # Aplicar Filtros
            view_df = full_library.copy()
            
            if sel_disc_view != "Todas":
                view_df = view_df[view_df['discipline_id'] == sel_disc_view]
            
            if sel_status_view:
                view_df = view_df[view_df['status'].isin(sel_status_view)]
            else:
                view_df = pd.DataFrame() # Sem filtro selecionado, não mostra nada ou mostraria tudo? Melhor seguir seleção.
            
            # Exibir
            if view_df.empty:
                st.info("Nenhuma habilidade encontrada com os filtros atuais.")
            else:
                st.markdown(f"**Encontrados: {len(view_df)} item(s)**")
                for idx, row in view_df.iterrows():
                    status_color = "green" if row['status'] == 'APPROVED' else "orange"
                    status_icon = "✅" if row['status'] == 'APPROVED' else "⏳"
                    
                    with st.expander(f"{status_icon} [{row['status']}] {row['bncc_code']} | {str(row['objective'])[:60]}..."):
                        st.markdown(f"**Disciplina:** {row['discipline_id']}")
                        st.markdown(f"**Objetivo Completo:** {row['objective']}")
                        st.markdown(f"**Autor:** {row['teacher_username']}")
                        st.divider()
                        st.markdown("##### 📏 Régua de Avaliação")
                        st.markdown(f"""
                        **N1 (1.0-2.9):** {row.get('desc_level_1', '-')}  
                        **N2 (3.0-5.9):** {row.get('desc_level_2', '-')}  
                        **N3 (6.0-7.9):** {row.get('desc_level_3', '-')}  
                        **N4 (8.0-10.0):** {row.get('desc_level_4', '-')}
                        """)





    # --- ABA 4: RELATÓRIOS (Atualizado) ---
    # --- ABA 4: RELATÓRIOS ---
    if tab_context == "tab4":
        # 0. MAPA DE SÉRIES (Reuso da lógica v3.40)
        setup_classes = get_static_data("setup_classes")
        map_class_grade = {}
        if not setup_classes.empty and 'grade' in setup_classes.columns:
            setup_classes['class_name'] = setup_classes['class_name'].astype(str).str.strip()
            setup_classes['grade'] = setup_classes['grade'].astype(str).str.strip()
            map_class_grade = dict(zip(setup_classes['class_name'], setup_classes['grade']))
        
        # Identificar séries do professor
        my_grades_rep = set()
        for t in allowed_classes:
            g = map_class_grade.get(t, "N/I")
            my_grades_rep.add(g)
        sorted_grades_rep = sorted(list(my_grades_rep))

        all_assessments = get_data("assessments")
        # Garantir colunas essenciais
        if 'discipline' not in all_assessments.columns: all_assessments['discipline'] = 'Geral'
        if 'class_name' not in all_assessments.columns: all_assessments['class_name'] = ""
        if 'grade_ref' not in all_assessments.columns: all_assessments['grade_ref'] = "N/I" # Fallback

        # Filtro inicial macro: Somente turmas permitidas
        class_assessments = all_assessments[all_assessments['class_name'].isin(allowed_classes)]
        
        if class_assessments.empty:
            st.info("Sem dados para as turmas permitidas.")
        else:
             # F1. Filtros Principais (Hierárquicos)
            # F1. Filtros Principais (Hierárquicos com opção "TODAS")
            c_rep1, c_rep2, c_rep3, c_rep4 = st.columns([1.5, 1.5, 1.5, 1.5])
            
            with c_rep1:
                # Filtro SÉRIE (Mantém seleção única para clareza inicial, ou todas?)
                # Vamos permitir "Todas" para o professor ver visão macro de seus anos
                grade_options = ["Todas"] + sorted_grades_rep
                grade_filter = st.selectbox("Série/Ano", grade_options, key="rep_grade")
            
            with c_rep2:
                # Filtro TURMA (Dependente da Série)
                if grade_filter == "Todas":
                    filtered_classes_rep = allowed_classes # Vê todas as suas turmas
                else:
                    filtered_classes_rep = [c for c in allowed_classes if map_class_grade.get(c, "N/I") == grade_filter]
                
                # Adicionar opção "Todas" se houver mais de uma turma
                if len(filtered_classes_rep) > 1:
                    class_options = ["Todas"] + filtered_classes_rep
                else:
                    class_options = filtered_classes_rep
                    
                if not class_options: class_options = ["Sem Turmas"]
                
                class_filter = st.selectbox("Turma", class_options, key="rep_class")
            
            with c_rep4:
                # Filtro de Bimestre (Mantém fixo ou Todas)
                bim_filter_rep = st.selectbox("Bimestre", ["Todos", "1º", "2º", "3º", "4º"], key="rep_bim_main")
            
            # F2. Filtro Disciplina
            with c_rep3:
                # ... (Lógica de loading de nomes mantida) ...
                setup_discs = get_static_data("setup_disciplines")
                dict_disc_names = {}
                if not setup_discs.empty:
                    setup_discs['discipline_id'] = setup_discs['discipline_id'].astype(str).str.strip().str.upper()
                    setup_discs['discipline_name'] = setup_discs['discipline_name'].astype(str).str.strip()
                    dict_disc_names = dict(zip(setup_discs['discipline_id'], setup_discs['discipline_name']))

                if not class_assessments.empty:
                    # Se "Todas" as turmas, pega disciplinas de todas elas
                    if class_filter == "Todas":
                         rel_classes = filtered_classes_rep # As disponíveis no filtro anterior
                    else:
                         rel_classes = [class_filter]
                         
                    available_disc_ids = class_assessments[class_assessments['class_name'].isin(rel_classes)]['discipline'].astype(str).str.strip().str.upper().unique()
                else:
                    available_disc_ids = []
                
                options_map_rep = {}
                for uid in available_disc_ids:
                    name = dict_disc_names.get(uid, uid)
                    options_map_rep[name] = uid
                
                # Adicionar "Todas" para Disciplinas também
                disc_options_keys = ["Todas"] + list(options_map_rep.keys())
                
                if not options_map_rep:
                    st.warning("Sem disciplinas.")
                    disc_filter = "N/A"
                else:
                    disc_filter_name = st.selectbox("Disciplina", disc_options_keys, key="rep_disc_name")
                    if disc_filter_name == "Todas":
                        disc_filter = "Todas"
                    else:
                        disc_filter = options_map_rep[disc_filter_name]


# ... (inside teacher_module)
                # Filtro de Data (Novo v3.54)
                d_col1, d_col2 = st.columns(2)
                # dt_ini = d_col1.date_input("De:", value=date(2026, 1, 1), format="DD/MM/YYYY") # Mantém fixo início do ano
                dt_ini = d_col1.date_input("De:", value=date(2026, 1, 1), format="DD/MM/YYYY", key="dt_ini_teacher_rep")
                
                # dt_fim = d_col2.date_input("Até:", value=date(2026, 12, 31), format="DD/MM/YYYY") # Antes
                dt_fim = d_col2.date_input("Até:", value=date.today(), format="DD/MM/YYYY", key="dt_fim_teacher_rep") # Fix v3.68: Data Atual

            # --- FILTRAGEM FINAL INTELIGENTE ---
            df_final = class_assessments.copy() # Começa com tudo que é permitido
            
            # 1. Filtro de Classe
            if class_filter != "Todas":
                # Normalização de Segurança (Strip para evitar mismatch por espaço)
                if not df_final.empty:
                    df_final['class_name'] = df_final['class_name'].astype(str).str.strip()
                
                class_filter_clean = str(class_filter).strip()
                
                # --- DEBUG CRÍTICO (REMOVER APÓS FIX) ---
                # st.warning(f"🔎 Debug Filtro Turma:")
                # st.write(f"Selecionado (Raw): {repr(class_filter)}")
                # st.write(f"Selecionado (Clean): {repr(class_filter_clean)}")
                # st.write(f"Turmas nos Dados (Amostra): {[repr(x) for x in df_final['class_name'].unique()]}")
                # ----------------------------------------
                
                df_final = df_final[df_final['class_name'] == class_filter_clean]
            else:
                # Se for "Todas", mas selecionou um Ano específico, filtra pelo Ano
                if grade_filter != "Todas":
                     # Filtrar turmas que sao do ano X
                     # Normaliza também para garantir
                     valid_classes_for_grade = [c for c in allowed_classes if map_class_grade.get(c, "N/I") == grade_filter]
                     df_final = df_final[df_final['class_name'].isin(valid_classes_for_grade)]
            
            # 2. Filtro de Disciplina
            if disc_filter != "Todas" and disc_filter != "N/A":
                 # Normalização de Segurança para garantir match
                 if 'discipline' in df_final.columns:
                     df_final['discipline'] = df_final['discipline'].astype(str).str.strip().str.upper()
                 
                 df_final = df_final[df_final['discipline'] == disc_filter]
                 
            # 3. Filtro de Bimestre
            if bim_filter_rep != "Todos":
                df_final = df_final[df_final['bimester_ref'] == bim_filter_rep]
            
            # Garante numérico e datas
            df_final['level_assigned'] = pd.to_numeric(df_final['level_assigned'], errors='coerce')
            df_final['level_numeric'] = df_final['level_assigned'].fillna(0) 
            df_final['date'] = pd.to_datetime(df_final['date'], errors='coerce')
            
            # FILTRO DE DATA (Aplicado após conversão)
            if not df_final.empty:
                df_final = df_final[
                    (df_final['date'].dt.date >= dt_ini) & 
                    (df_final['date'].dt.date <= dt_fim)
                ]
            
            # ... (Merge com Rubricas mantido - Código já existente) ...
            if 'rubric_id' in df_final.columns:
                 df_rubrics_ref = get_data("teacher_rubrics")
                 if not df_rubrics_ref.empty and 'rubric_id' in df_rubrics_ref.columns and 'objective' in df_rubrics_ref.columns:
                     df_final['rubric_id'] = df_final['rubric_id'].astype(str).str.strip()
                     df_rubrics_ref['rubric_id'] = df_rubrics_ref['rubric_id'].astype(str).str.strip()
                     df_final = df_final.merge(df_rubrics_ref[['rubric_id', 'objective']], on='rubric_id', how='left', suffixes=('', '_rubric'))
                     if 'objective_rubric' in df_final.columns:
                         df_final['objective'] = df_final['objective_rubric'].fillna(df_final.get('objective', 'Objetivo não encontrado'))
            
            # NORMALIZAÇÃO CRÍTICA DE IDS (Movidp para cá na v3.62 para afetar Visão Aluno/Histórico)
            if not df_final.empty and 'student_id' in df_final.columns:
                df_final['student_id'] = df_final['student_id'].astype(str).str.replace('.0', '', regex=False).str.strip()

            # Definir df_history (Dados crus para gráficos temporais)
            df_history = df_final.copy()
            if 'objective' not in df_history.columns:
                 df_history['objective'] = "Objetivo não registrado"
            
            # ... (Sanity Check mantido) ...
            required_cols = ['student_id', 'bncc_code', 'objective', 'level_numeric']
            missing_cols = [c for c in required_cols if c not in df_history.columns and c != 'objective'] 
            if missing_cols:
                st.error(f"⚠️ Erro de Dados: {missing_cols}")
                st.stop()
                
            if df_final.empty:
                st.info("Nenhum dado encontrado.")
            else:
                # ==============================================================================
                # DASHBOARD GLOBAL MULTIDIMENSIONAL (v3.50)
                # ==============================================================================
                
                tab_g1, tab_g2, tab_g3, tab_g4 = st.tabs([
                    "📈 Trajetória Comparativa", # Renomeado
                    "🌡️ Mapa da Turma", 
                    "👤 Visão Aluno",
                    "📝 Fechamento" 
                ])
                
                # --- 1. TRAJETÓRIA COMPARATIVA (TODAS v3.50) ---
                with tab_g1:
                    st.markdown("### 🌍 Análise de Trajetória (Comparativa)")
                    st.caption("Acompanhe a evolução da média acumulada. Compare turmas ou disciplinas selecionando 'Todas' nos filtros.")
                    
                    if df_history.empty:
                         st.warning("Sem dados.")
                    else:
                         # Definição Dinâmica de Grupos para o Gráfico
                         # Se selecionou "Todas as Turmas", agrupa por Turma (para gerar linhas coloridas)
                         # Se selecionou "Uma Turma" e "Todas as Disciplinas", agrupa por Disciplina
                         # Se tudo específico, é uma linha só.
                         
                         group_col = None
                         group_title = "Geral"
                         
                         if class_filter == "Todas":
                             group_col = 'class_name'
                             group_title = "Turmas"
                         elif disc_filter == "Todas":
                             group_col = 'discipline'
                             group_title = "Disciplinas"
                         
                         import plotly.express as px
                         
                         # Preparar dados: Agrupar por Data + Grupo (se houver)
                         if group_col:
                             # Agrupa por Data E pelo Grupo (ex: Turma A dia 10, Turma B dia 10)
                             df_evo = df_history.groupby(['date', group_col]).agg({
                                 'level_numeric': 'mean',
                                 'objective': lambda x: ' | '.join(x.unique()[:1]), # Pega o primeiro objetivo do dia para tooltip
                                 'bncc_code': lambda x: ' | '.join(x.unique()[:1])
                             }).reset_index()
                             
                             # Calcular Acumulado POR GRUPO
                             df_evo['media_acumulada'] = df_evo.groupby(group_col)['level_numeric'].expanding().mean().reset_index(level=0, drop=True)
                             
                             fig_global = px.line(
                                 df_evo,
                                 x='date',
                                 y='media_acumulada',
                                 color=group_col, # Várias linhas!
                                 title=f"Evolução Comparativa por {group_title}",
                                 labels={'date': 'Data', 'media_acumulada': 'Média Acumulada', group_col: group_title},
                                 range_y=[0.5, 4.5],
                                 markers=True,
                                 hover_data={'objective': True, 'bncc_code': True} # O Contexto Pedagógico no Mouse!
                             )
                         else:
                             # Linha Única (Comportamento antigo, mas com Tooltip rico)
                             df_evo = df_history.groupby('date').agg({
                                 'level_numeric': 'mean',
                                 'objective': lambda x: ' | '.join(x.unique()[:1]),
                                 'bncc_code': lambda x: ' | '.join(x.unique()[:1])
                             }).reset_index()
                             
                             df_evo['media_acumulada'] = df_evo['level_numeric'].expanding().mean()
                             
                             fig_global = px.line(
                                 df_evo,
                                 x='date',
                                 y='media_acumulada',
                                 title="Trajetória Global da Turma/Disciplina",
                                 labels={'date': 'Data', 'media_acumulada': 'Média Acumulada'},
                                 range_y=[0.5, 4.5],
                                 markers=True,
                                 hover_data={'objective': True, 'bncc_code': True}
                             )
                             fig_global.update_traces(line_color='#FF5722', line_width=4)

                         fig_global.add_hline(y=3, line_dash="dot", line_color="green", annotation_text="Meta (3.0)")
                         st.plotly_chart(fig_global, use_container_width=True)
                         
                         st.info("💡 Dica: Passe o mouse sobre os pontos da linha para ver qual Habilidade/Objetivo causou a oscilação na nota.")

                # --- 2. VISÃO GERAL DA TURMA (HEATMAP) ---
                with tab_g2:
                    st.markdown("### 🌡️ Mapa de Calor da Turma")
                    st.caption("Identifique rapidamente alunos com dificuldades gerais (Média < 2.0 em Vermelho).")
                    st.info("ℹ️ Ordenado por Desempenho: Alunos com maiores dificuldades estão na **base** do gráfico.")
                    
                    if not 'student_map' in locals():
                        all_students = get_data("students")
                        student_map = {}
                        if not all_students.empty:
                            all_students['student_id'] = all_students['student_id'].astype(str).str.replace('.0', '')
                            student_map = dict(zip(all_students['student_id'], all_students['student_name']))
                    
                    # Garantir lista completa de alunos da turma selecionada
                    current_class_students = []
                    if class_filter != "Todas":
                        all_st = get_data("students")
                        if not all_st.empty:
                            # Filtra pela turma atual e NORMALIZA IDs (Fix v3.61: .str.replace)
                            current_class_students = all_st[all_st['class_name'] == class_filter]['student_id'].astype(str).str.replace('.0', '', regex=False).str.strip().unique().tolist()
                            
                            # DEBUG TEMPORÁRIO (REMOVER DEPOIS)
                            # st.caption(f"🔍 DEBUG: Total de Alunos em '{class_filter}' (Planilha Students): {len(current_class_students)}")
                            # if len(current_class_students) < 10: # Se for muito pouco, listar
                            #     st.caption(f"IDs Encontrados: {current_class_students}")
                                
                    # Pivot: Linhas=Alunos (Nome), Colunas=Habilidades
                    # CORREÇÃO: Normalizar student_id no df_final antes do pivot para garantir match com current_class_students
                    if not df_final.empty:
                        # NORMALIZAÇÃO CRÍTICA DE IDS (Já feita acima na v3.62)
                        # df_final['student_id'] = df_final['student_id'].astype(str).str.replace('.0','', regex=False).str.strip()
                        
                        # GARANTIA NUMÉRICA
                        # Se level_numeric não existir ou for object, recriar/converter
                        if 'level_numeric' not in df_final.columns:
                             # Tenta converter level_assigned se existir
                             if 'level_assigned' in df_final.columns:
                                 df_final['level_numeric'] = pd.to_numeric(df_final['level_assigned'], errors='coerce')
                        else:
                             df_final['level_numeric'] = pd.to_numeric(df_final['level_numeric'], errors='coerce')

                        # CALCULAR MÉDIA REAL (Baseada em Habilidades, não em volume de avaliações)
                        # 1. Agrupa por Aluno + BNCC e tira média da Habilidade
                        # 2. Agrupa por Aluno e tira média das Habilidades
                        df_for_mean = df_final.copy()
                        df_for_mean['level_numeric'] = df_for_mean['level_numeric'].replace(0, np.nan)
                        
                        # Média por Habilidade
                        skill_means = df_for_mean.groupby(['student_id', 'bncc_code'])['level_numeric'].mean().reset_index()
                        
                        # Média do Aluno (Média das Médias das Habilidades)
                        real_means = skill_means.groupby('student_id')['level_numeric'].mean()
                    else:
                        real_means = pd.Series(dtype=float)
                    
                    pivot_table = df_final.pivot_table(
                        index='student_id', 
                        columns='bncc_code', 
                        values='level_numeric',
                        aggfunc='mean'
                    ).fillna(0)
                    
                    # --- DEBUG PROVISÓRIO (Análise de Dados) ---
                    # with st.expander("🕵️‍♂️ Debug de Dados (Não visível para usuário final)"):
                    #    st.write("Amostra do df_final (Antes do Pivot):")
                    #    st.dataframe(df_final.head())
                    #    st.write("Tipos de Dados:")
                    #    st.write(df_final.dtypes)
                    #    st.write(f"IDs no df_final: {df_final['student_id'].unique().tolist()}")
                    #    st.write(f"IDs na Lista da Turma: {current_class_students}")
                    #    st.write(f"Interseção: {list(set(df_final['student_id'].unique()) & set(current_class_students))}")

                    
                    # --- REINDEX PARA INCLUIR TODOS OS ALUNOS (Mesmo sem nota) ---
                    if current_class_students:
                        # Adiciona alunos que não estão no pivot com NaN (que vira 0)
                        # Garante que usamos SOMENTE os IDs da lista oficial da turma (current_class_students)
                        pivot_table = pivot_table.reindex(current_class_students, fill_value=0)
                        
                        # DEBUG TEMPORÁRIO
                        # st.caption(f"🔍 DEBUG: Total de Alunos no Gráfico (Pós-Processamento): {len(pivot_table)}")

                    # --- ORDENAÇÃO INTELIGENTE (v3.56 - Alinhado com Fechamento) ---
                    # Usar a média real (real_means) para ordenar. 
                    # Alunos sem nota (NaN em real_means) ficarão no final com fillna(-1)
                    
                    # Garantir que todos do pivot tenham uma média (mesmo que 0 se não existia em real_means)
                    sorted_index = real_means.reindex(pivot_table.index).fillna(-1).sort_values(ascending=False).index
                    pivot_table = pivot_table.reindex(sorted_index)
                    # -------------------------------------
                    
                    # Nomear linhas com nomes dos alunos (Index Mapping Seguro)
                    new_index = []
                    seen_names = {}
                    
                    for sid in pivot_table.index:
                        sid_clean = str(sid).replace('.0', '')
                        original_name = student_map.get(sid_clean, sid)
                        # Verifica se é None
                        if pd.isna(original_name): original_name = sid_clean
                        
                        # Tratamento de Nomes Duplicados Visualmente
                        final_name = original_name
                        if final_name in seen_names:
                            # Se já existe, adiciona o ID para diferenciar
                            final_name = f"{original_name} ({sid_clean})"
                            # Atualiza o anterior também para ficar claro? (Complexo, melhor só diferenciar o atual)
                        
                        seen_names[final_name] = True
                        new_index.append(final_name)
                    
                    pivot_table.index = new_index
                    
                    # Calcular Altura Dinâmica
                    # 30px por aluno + 150px de margem (Labels, Title)
                    dyn_height = max(450, len(pivot_table) * 30 + 150)

                    # Heatmap usando px.imshow
                    # Cores: Vermelho (1) -> Amarelo (2.5) -> Verde (4)
                    
                    # Preparar texto para exibição (substituir 0.0 por '-')
                    text_values = pivot_table.round(1).astype(str).replace(['0.0', '0'], '-')
                    
                    fig_heat = px.imshow(
                        pivot_table,
                        labels=dict(x="Habilidade", y="Aluno", color="Nível Médio"),
                        x=pivot_table.columns,
                        y=pivot_table.index,
                        color_continuous_scale=['#d32f2f', '#fbc02d', '#388e3c'], 
                        range_color=[1, 4],
                        aspect="auto",
                        text_auto=False
                    )
                    fig_heat.update_traces(text=text_values, texttemplate="%{text}")
                    fig_heat.update_layout(height=dyn_height) # Altura forçada
                    st.plotly_chart(fig_heat, use_container_width=True)
                    
                    # --- DEBUG VISUAL AVANÇADO (Solicitado para verificação) ---
                    # with st.expander("🕵️‍♂️ Debug Avançado: Auditoria de Alunos"):
                    #     st.write(f"**Total Esperado (Planilha Students):** {len(current_class_students)}")
                    #     st.write(f"**Total no Gráfico (Pivot Table):** {len(pivot_table)}")
                    #     
                    #     set_expected = set(current_class_students)
                    #     set_actual = set(pivot_table.index) # Note: index aqui já são NOMES, então precisamos comparar com cuidado ou usar o anterior
                    #     
                    #     # Recriar ID map reverso para conferência
                    #     # O pivot_table.index agora são NOMES. Precisamos ver se perdemos alguém na conversão de ID->Nome
                    #     # Mas o reindex foi feito com IDs.
                    #     
                    #     st.write("---")
                    #     st.write("##### IDs que entraram no Reindex:")
                    #     st.code(str(current_class_students))
                    #     
                    #     st.write("##### Linhas do Pivot (IDs ou Nomes?):")
                    #     st.code(str(pivot_table.index.tolist()))
                    #     
                    #     if len(pivot_table) != len(current_class_students):
                    #         st.error(f"⚠️ DISCREPÂNCIA DETECTADA: {len(current_class_students) - len(pivot_table)} alunos perdidos.")
                    #     else:
                    #         st.success("✅ Contagem está batendo (30 vs 30). Se não vê no gráfico, pode ser corte visual.")


                # --- 3. DIAGNÓSTICO PEDAGÓGICO (v3.52) ---
                with tab_g3:
                    st.markdown("### 👤 Diagnóstico Pedagógico do Aluno")
                    st.caption("Visão aprofundada do desempenho, pontos fortes e áreas de atenção por disciplina.")
                    
                    # Seletor de aluno
                    all_ids = sorted(df_final['student_id'].unique())
                    # Helper para display
                    def get_label(sid):
                        sid_clean = str(sid).replace('.0','')
                        return f"{student_map.get(sid_clean, sid_clean)}"

                    sel_aluno_id = st.selectbox("Selecione o Aluno:", all_ids, format_func=get_label)
                    
                    # CORREÇÃO: Usar df_history para ver TODOS os pontos no tempo
                    df_aluno = df_history[df_history['student_id'] == sel_aluno_id].copy()
                    
                    if df_aluno.empty:
                        st.info("Sem dados para este aluno nestes filtros.")
                    else:
                        df_aluno = df_aluno.sort_values('date')
                        
                        # --- CARDS DE RESUMO ---
                        media_geral = df_aluno['level_numeric'].mean()
                        total_avals = len(df_aluno)
                        habilidades_total = df_aluno['bncc_code'].nunique()
                        
                        # Melhor e Pior Disciplina (se houver mais de uma)
                        disc_stats = df_aluno.groupby('discipline')['level_numeric'].mean()
                        best_disc = disc_stats.idxmax()
                        worst_disc = disc_stats.idxmin()
                        
                        c_metric1, c_metric2, c_metric3, c_metric4 = st.columns(4)
                        c_metric1.metric("Média Global", f"{media_geral:.1f}", delta=f"{media_geral-3.0:.1f} vs Meta")
                        c_metric2.metric("Avaliações", total_avals)
                        c_metric3.metric("Habilidades", habilidades_total)
                        c_metric4.metric("Destaque em", best_disc)
                        st.divider()

                        # --- REPORT TEXTUAL INTELIGENTE (GERADO POR REGRA) ---
                        st.subheader("📑 Relatório de Situação")
                        
                        with st.container(border=True):
                            # Identificar Disciplinas
                            discs_aluno = df_aluno['discipline'].unique()
                            
                            report_lines = []
                            report_lines.append(f"**Resumo Geral:** O aluno possui média **{media_geral:.1f}** em {len(discs_aluno)} disciplinas analisadas.")
                            
                            for d in discs_aluno:
                                df_d = df_aluno[df_aluno['discipline'] == d]
                                m_d = df_d['level_numeric'].mean()
                                
                                # Análise por Habilidade nesta disciplina
                                skill_stats = df_d.groupby('bncc_code')['level_numeric'].mean()
                                strengths = skill_stats[skill_stats >= 3.0].index.tolist()
                                weak = skill_stats[skill_stats < 2.5].index.tolist() # < 2.5 é atenção
                                
                                status_disc = "🟢 Ótimo" if m_d >= 3.5 else "🟡 Regular" if m_d >= 2.5 else "🔴 Atenção"
                                
                                txt_disc = f"**{d} ({status_disc} - {m_d:.1f}):**"
                                if strengths:
                                    txt_disc += f"  \n   *Pontos Fortes:* {', '.join(strengths[:3])}"
                                if weak:
                                    txt_disc += f"  \n   *Atenção em:* {', '.join(weak[:3])}"
                                elif not weak and m_d >= 3.0:
                                    txt_disc += "  \n   *Aluno consistente, sem quedas graves.*"
                                
                                report_lines.append(txt_disc)
                            
                            st.markdown("\n\n".join(report_lines))

                        st.divider()

                        # --- GRÁFICOS (TAB & COLUMN LAYOUT) ---
                        col_g1, col_g2 = st.columns([1.5, 1])
                        
                        with col_g1:
                            st.markdown("#### 📈 Evolução Temporal (Por Disciplina)")
                            
                            with st.expander("ℹ️ Como ler este gráfico?"):
                                st.markdown("""
                                - **Linha Colorida:** Representa a média acumulada de **uma disciplina específica**.
                                - **Independência:** A nota de Matemática não interfere na linha de História.
                                - **Tendência:** Se a linha sobe, o aluno está evoluindo naquela matéria. Se desce, requer atenção.
                                """)

                            # EVOLUÇÃO (LINHA) - CÁLCULO SEGREGADO POR DISCIPLINA
                            # 1. Agrupar por Disciplina e calcular a média acumulada DENTRO de cada grupo
                            # Isso garante que a nota de Mat não afete a média acumulada de História
                            
                            # Ordenar por data
                            df_aluno = df_aluno.sort_values('date')
                            
                            # Calcular média acumulada POR GRUPO DE DISCIPLINA
                            # Transform: retorna série com mesmo index, perfeito para atribuir de volta
                            df_aluno['media_acumulada_disciplina'] = df_aluno.groupby('discipline')['level_numeric'].transform(lambda x: x.expanding().mean())

                            import plotly.express as px
                            fig_evo = px.line(
                                df_aluno, 
                                x='date', 
                                y='media_acumulada_disciplina', # Usa a média segregada
                                markers=True,
                                color='discipline', # Uma linha por disciplina
                                range_y=[0.5, 4.5],
                                title="Evolução Independente por Disciplina",
                                hover_data={'bncc_code': True, 'objective': True}
                            )
                            fig_evo.add_hline(y=3, line_dash="dot", line_color="green", annotation_text="Meta (3.0)")
                            st.plotly_chart(fig_evo, use_container_width=True)

                        with col_g2:
                            st.markdown("#### 📊 Desempenho por Habilidade (BNCC)")
                            with st.expander("ℹ️ O que isso mostra?"):
                                st.caption("Cada barra é a média exclusiva dos objetivos daquela habilidade. Elas não se misturam.")
                                
                            # DESEMPENHO POR HABILIDADE (BARRAS)
                            # Agrupar por BNCC e Disciplina (Garante que códigos iguais de matérias dif - raro - não se misturem)
                            skill_perf = df_aluno.groupby(['bncc_code', 'discipline'])['level_numeric'].mean().reset_index()
                            skill_perf = skill_perf.sort_values('level_numeric', ascending=True)
                            
                            fig_bar = px.bar(
                                skill_perf,
                                x='level_numeric',
                                y='bncc_code',
                                orientation='h',
                                color='level_numeric',
                                color_continuous_scale=['#d32f2f', '#fbc02d', '#388e3c'],
                                range_color=[1, 4],
                                range_x=[0, 4.5],
                                text_auto='.1f',
                                title="Média Isolada por Habilidade",
                                labels={'level_numeric': 'Média', 'bncc_code': 'Código BNCC'}
                            )
                            st.plotly_chart(fig_bar, use_container_width=True)
                            
                        # --- TABELA DETALHADA ---
                        with st.expander("📋 Ver Histórico Detalhado de Avaliações", expanded=False):
                            st.dataframe(
                                df_aluno[['date', 'discipline', 'bncc_code', 'objective', 'level_numeric', 'teacher']].sort_values('date', ascending=False),
                                column_config={
                                    "date": st.column_config.DateColumn("Data"),
                                    "discipline": "Disciplina",
                                    "bncc_code": "Habilidade",
                                    "objective": "Objetivo",
                                    "level_numeric": st.column_config.NumberColumn("Nota", format="%.1f"),
                                    "teacher": "Prof. Resp."
                                },
                                use_container_width=True,
                                hide_index=True
                            )



                # --- 4. FECHAMENTO BIMESTRAL ---
                with tab_g4:
                    st.markdown("### 📅 Fechamento Bimestral")
                    
                    sel_bim_close = st.selectbox("Bimestre", ["1º", "2º", "3º", "4º"], key="bim_close_sel")
                    df_bim = df_final[df_final['bimester_ref'] == sel_bim_close]
                    
                    if df_bim.empty:
                        st.info(f"Sem avaliações para o {sel_bim_close} bimestre.")
                    else:
                        # Excluir zeros da média (Zeros = não avaliado)
                        df_bim_calc = df_bim.copy()
                        df_bim_calc['level_assigned'] = pd.to_numeric(df_bim_calc['level_assigned'], errors='coerce').fillna(0)
                        df_bim_calc['level_assigned'] = df_bim_calc['level_assigned'].replace(0, np.nan)
                        
                        # 1. Média por Habilidade (BNCC)
                        skill_means_bim = df_bim_calc.groupby(['student_id', 'bncc_code'])['level_assigned'].mean().reset_index()
                        
                        # 2. Média do Aluno (Média das Habilidades)
                        bim_grp = skill_means_bim.groupby(['student_id'])['level_assigned'].mean().reset_index()
                        # Merge name
                        bim_grp['student_name'] = bim_grp['student_id'].astype(str).str.replace('.0','').map(student_map).fillna(bim_grp['student_id'])
                        
                        # Conversão Numérica (Nota 0-10)
                        bim_grp['Média (0-10)'] = (bim_grp['level_assigned'] * 2.5).clip(upper=10.0)
                        
                        # Formatação para Exibição
                        # Converter NaN na Média para '-'
                        df_display = bim_grp[['student_name', 'level_assigned', 'Média (0-10)']] \
                            .sort_values('Média (0-10)', ascending=False) \
                            .rename(columns={'student_name': 'Aluno', 'level_assigned': 'Nível Médio'})
                        
                        # Aplicar formatação condicional apenas para exibição (mantendo valores numéricos para sort se possível, mas aqui já ordenamos)
                        # Na verdade, para exibir misturado (número e texto), precisamos converter tudo para string ou usar Styler.
                        # Vamos usar converter para string onde for NaN
                        
                        df_display['Nível Médio'] = df_display['Nível Médio'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) and x > 0 else "-")
                        df_display['Média (0-10)'] = df_display['Média (0-10)'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) and x > 0 else "-")

                        st.dataframe(
                            df_display,
                            use_container_width=True,
                            hide_index=True
                        )


            # ... (Closing Tab section end)



# ==============================================================================
# MAIN APP FLOW
# ==============================================================================

# ==============================================================================
# 9. MÓDULO DO COORDENADOR (DASHBOARD)
# ==============================================================================
def coordinator_module(user_info):
    st.markdown(f"## 🏛️ Painel da Coordenação: **{user_info['name']}**")
    
    if st.button("Sair", key="logout_btn_coord"):
        st.session_state["logged_in"] = False
        st.rerun()
        
    st.divider()
    
    # Carregar Dados Gerais
    df_assessments = get_data("assessments")
    df_rubrics = get_data("teacher_rubrics")
    df_students = get_data("students")
    
    # Converter datas e números
    if not df_assessments.empty:
        df_assessments['level_assigned'] = pd.to_numeric(df_assessments['level_assigned'], errors='coerce')
        df_assessments['date'] = pd.to_datetime(df_assessments['date'], errors='coerce')
        # Garantir colunas
        if 'discipline' not in df_assessments.columns: df_assessments['discipline'] = 'GERAL'
        if 'class_name' not in df_assessments.columns: df_assessments['class_name'] = 'N/A'

    
    tab_c1, tab_c2, tab_c3 = st.tabs(["🏢 Visão Escola", "🏫 Visão Turma", "🎓 Visão Aluno"])
    
    # --- VISÃO 1: ESCOLA ---
    with tab_c1:
        st.subheader("Panorama Geral da Escola")
        
        if df_assessments.empty:
            st.warning("Sem dados de avaliações para gerar indicadores.")
        else:
            # 1. Média Geral por Disciplina (Gráfico de Barras)
            avg_per_disc = df_assessments.groupby('discipline')['level_assigned'].mean().reset_index()
            
            if avg_per_disc.empty:
                st.info("Dados de avaliações insuficientes para gerar média por disciplina.")
            else:
                avg_per_disc['level_assigned'] = avg_per_disc['level_assigned'].round(2)
                
                fig_bar = px.bar(
                    avg_per_disc, 
                    x='discipline', 
                    y='level_assigned',
                    title="Média de Proficiência por Disciplina (Nível 1-4)",
                    color='level_assigned',
                    color_continuous_scale='RdYlGn',
                    range_y=[0, 4.5],
                    text='level_assigned'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # 2. Adesão dos Professores (Rubricas criadas)
            if not df_rubrics.empty:
                if 'status' not in df_rubrics.columns: df_rubrics['status'] = 'APPROVED'
                
                # Preencher NaNs para evitar drop no groupby
                if 'discipline_id' in df_rubrics.columns:
                     df_rubrics['discipline_id'] = df_rubrics['discipline_id'].fillna('GERAL').astype(str).replace('', 'GERAL')
                else:
                     df_rubrics['discipline_id'] = 'GERAL'
                     
                if 'teacher_username' in df_rubrics.columns:
                     df_rubrics['teacher_username'] = df_rubrics['teacher_username'].fillna('Desconhecido').astype(str)
                else:
                     df_rubrics['teacher_username'] = 'Desconhecido'
                
                # Contar rubricas por prof e disciplina
                rubrics_count = df_rubrics.groupby(['discipline_id', 'teacher_username'])['rubric_id'].count().reset_index()
                
                if rubrics_count.empty:
                    st.info("Sem dados de adesão (Réguas criadas).")
                else:
                    try:
                        fig_tree = px.treemap(
                            rubrics_count, 
                            path=['discipline_id', 'teacher_username'], 
                            values='rubric_id',
                            title="Volume de Réguas Criadas (Adesão ao Planejamento)"
                        )
                        st.plotly_chart(fig_tree, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Erro ao gerar gráfico de adesão: {e}")
            else:
                st.info("Nenhuma régua criada ainda para medir adesão.")

    # --- VISÃO 2: TURMA ---
    with tab_c2:
        st.subheader("Análise por Turma")
        
        if df_assessments.empty:
             st.warning("Sem dados.")
        else:
            all_classes = sorted(df_assessments['class_name'].astype(str).unique())
            sel_class_coord = st.selectbox("Selecione a Turma:", all_classes, key="sel_class_coord")
            
            # Filtrar
            df_class = df_assessments[df_assessments['class_name'] == sel_class_coord]
            
            if df_class.empty:
                st.warning(f"Sem avaliações para a turma {sel_class_coord}.")
            else:
                c_res1, c_res2 = st.columns(2)
                
                # A. Distribuição de Níveis
                with c_res1:
                    dist_levels = df_class['level_assigned'].value_counts().reset_index()
                    dist_levels.columns = ['Nível', 'Qtd']
                    
                    fig_pie = px.pie(dist_levels, values='Qtd', names='Nível', title=f"Distribuição de Níveis - {sel_class_coord}", hole=0.4)
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # B. Alunos em Risco (Média < 2.0)
                with c_res2:
                    st.markdown("##### 🚨 Alunos em Atenção (Média < 2.0)")
                    try:
                        # Converter ID para string limpa para merge
                        df_class['student_id'] = df_class['student_id'].astype(str).str.replace('.0', '')
                        
                        # Média por aluno
                        avg_student = df_class.groupby('student_id')['level_assigned'].mean().reset_index()
                        
                        # Cruzar com nomes
                        if not df_students.empty:
                             # Limpar ID estudantes DB
                             df_students['student_id_clean'] = df_students['student_id'].astype(str).str.replace('.0', '')
                             avg_student = avg_student.merge(
                                 df_students[['student_id_clean', 'student_name']], 
                                 left_on='student_id', 
                                 right_on='student_id_clean', 
                                 how='left'
                             )
                             avg_student['student_name'] = avg_student['student_name'].fillna(avg_student['student_id'])
                        else:
                            avg_student['student_name'] = avg_student['student_id']
                        
                        # Filtrar Risco
                        risk_students = avg_student[avg_student['level_assigned'] < 2.0].sort_values('level_assigned')
                        
                        if risk_students.empty:
                            st.success("Nenhum aluno com média abaixo de 2.0 nesta turma! 🎉")
                        else:
                            st.dataframe(
                                risk_students[['student_name', 'level_assigned']].style.format({'level_assigned': '{:.2f}'}),
                                use_container_width=True,
                                hide_index=True
                            )
                    except Exception as e:
                        st.error(f"Erro ao calcular risco: {e}")

    # --- VISÃO 3: ALUNO ---
    # --- VISÃO 3: ALUNO (DIAGNÓSTICO AVANÇADO) ---
    with tab_c3:
        st.subheader("Ficha Individual do Aluno (Diagnóstico)")
        
        # Search global
        if df_students.empty:
            st.warning("Base de alunos vazia.")
        else:
            # Selectbox com busca
            df_students['search_label'] = df_students['student_name'].astype(str) + " (" + df_students['class_name'].astype(str) + ")"
            all_students_opts = df_students['search_label'].tolist()
            
            sel_student_str = st.selectbox("Buscar Aluno:", all_students_opts, key="coord_student_search")
            
            if sel_student_str:
                # Recuperar ID
                sel_st_row = df_students[df_students['search_label'] == sel_student_str].iloc[0]
                sel_st_id = str(sel_st_row['student_id']).replace('.0', '')
                
                st.info(f"Analisando: **{sel_st_row['student_name']}** | Turma: {sel_st_row['class_name']}")
                
                # Filtrar avaliações
                if not df_assessments.empty:
                    df_assessments['student_id'] = df_assessments['student_id'].astype(str).str.replace('.0', '')
                    
                    df_st_hist = df_assessments[df_assessments['student_id'] == sel_st_id].copy()
                    
                    if df_st_hist.empty:
                        st.warning("Este aluno ainda não possui avaliações registradas.")
                    else:
                        df_st_hist['date'] = pd.to_datetime(df_st_hist['date'])
                        df_st_hist = df_st_hist.sort_values('date')
                        
                        # --- 1. SAÚDE ACADÊMICA (Média Acumulada Geral) ---
                        st.markdown("#### 🏥 Saúde Acadêmica (Média Geral Acumulada)")
                        
                        # Média Acumulada de TUDO
                        df_st_hist['global_cum_mean'] = df_st_hist['level_assigned'].expanding().mean()
                        
                        curr_gpa = df_st_hist['global_cum_mean'].iloc[-1]
                        
                        col_metrics1, col_metrics2 = st.columns([1, 4])
                        with col_metrics1:
                            st.metric("Nota Geral Atual (1-4)", f"{curr_gpa:.2f}")
                            if curr_gpa < 2:
                                st.error("Alerta Vermelho")
                            elif curr_gpa < 3:
                                st.warning("Atenção")
                            else:
                                st.success("Bom Desempenho")
                        
                        with col_metrics2:
                            fig_health = px.line(df_st_hist, x='date', y='global_cum_mean', markers=True, 
                                               title="Curva de Consistência Geral (Todas as Disciplinas)")
                            fig_health.add_hline(y=3, line_dash="dash", line_color="green", annotation_text="Meta (3.0)")
                            fig_health.update_yaxes(range=[0.5, 4.5], title="Média Acumulada")
                            st.plotly_chart(fig_health, use_container_width=True)

                        st.divider()

                        # --- 2. HEATMAP TEMPORAL (DISCIPLINA x BIMESTRE) ---
                        st.markdown("#### 🌡️ Mapa de Calor (Disciplina x Bimestre)")
                        st.caption("Identifique falhas específicas por matéria ao longo do ano.")
                        
                        # Agrupar por Disciplina e Bimestre
                        # Usar bimester_ref se disponível, ou mês da data
                        if 'bimester_ref' in df_st_hist.columns:
                            col_time = 'bimester_ref'
                        else:
                            df_st_hist['month'] = df_st_hist['date'].dt.month_name()
                            col_time = 'month'
                        
                        pivot_disc = df_st_hist.pivot_table(
                            index='discipline', 
                            columns=col_time, 
                            values='level_assigned', 
                            aggfunc='mean'
                        )
                        
                        # Ordenar colunas de tempo se for bimestre
                        if col_time == 'bimester_ref':
                            # Garantir ordem 1, 2, 3, 4
                            cols_order = [c for c in ["1º", "2º", "3º", "4º"] if c in pivot_disc.columns]
                            pivot_disc = pivot_disc[cols_order]
                        
                        fig_heat_disc = px.imshow(
                            pivot_disc,
                            labels=dict(x="Período", y="Disciplina", color="Média"),
                            color_continuous_scale=['#d32f2f', '#fbc02d', '#388e3c'], 
                            range_color=[1, 4],
                            text_auto=".1f",
                            aspect="auto"
                        )
                        st.plotly_chart(fig_heat_disc, use_container_width=True)
                        
                        with st.expander("Ver dados brutos"):
                            st.dataframe(df_st_hist[['date', 'discipline', 'bncc_code', 'level_assigned']].sort_values('date', ascending=False))
    
def main():
    if login():
        user = st.session_state["user_info"]
        
        # Sidebar simplificado
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=50)
            st.caption("v3.69 (Fix Duplicate Widget)")
            # --- ÁREA DE TESTE (MOCK DATA) ---
            if user['role'] in ['admin', 'coordinator']:
                with st.expander("🛠️ Ferramentas de Teste", expanded=False):
                    st.warning("Cuidado: Isso vai adicionar MUITOS dados.")
                    if st.button("🧪 Gerar Dados Fictícios (5 Turmas)", key="btn_mock_gen"):
                        try:
                            import mock_data_generator
                            st.info("Gerando dados... Aguarde (pode demorar uns segundos)...")
                            
                            df_cls, df_stu, df_rub, df_ass = mock_data_generator.generate_mock_data()
                            
                            # Concatenar com dados existentes (ou criar se vazio)
                            # 1. Classes
                            curr_cls = get_data("setup_classes")
                            if curr_cls.empty: 
                                new_cls = df_cls
                            else:
                                new_cls = pd.concat([curr_cls, df_cls]).drop_duplicates(subset=['class_name'], keep='last')
                            save_data(new_cls, "setup_classes")
                            
                            # 2. Students
                            curr_stu = get_data("students")
                            # Filtrar apenas colunas compatíveis
                            if not curr_stu.empty:
                                new_stu = pd.concat([curr_stu, df_stu]).drop_duplicates(subset=['student_id'], keep='last')
                            else:
                                new_stu = df_stu
                            save_data(new_stu, "students")
                            
                            # 3. Rubricas
                            curr_rub = get_data("teacher_rubrics")
                            if not curr_rub.empty:
                                new_rub = pd.concat([curr_rub, df_rub]).drop_duplicates(subset=['rubric_id'], keep='last')
                            else:
                                new_rub = df_rub
                            save_data(new_rub, "teacher_rubrics")
                            
                            # 4. Avaliações (Essas só adicionam, não removem duplicatas simples)
                            curr_ass = get_data("assessments")
                            if not curr_ass.empty:
                                new_ass = pd.concat([curr_ass, df_ass], ignore_index=True)
                            else:
                                new_ass = df_ass
                            save_data(new_ass, "assessments")
                            
                            st.success(f"✅ Sucesso! Gerados: {len(df_stu)} alunos, {len(df_rub)} rubricas e {len(df_ass)} avaliações.")
                            st.balloons()
                            
                        except Exception as e:
                            st.error(f"Erro na geração: {e}")
            # 3. Layout: Nome no Sidebar ao invés de Header GIGANTE
            st.write(f"Olá, **{user['name']}**")
            
            # Botão de Recarregar Dados (Para forçar leitura de novas colunas)
            if st.button("🔄 Recarregar Dados (Limpar Cache)"):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.rerun()
            
            if st.button("Sair"):
                st.session_state["logged_in"] = False
                st.rerun()
        
        if user['role'].lower() == 'admin':
            admin_module()
        elif user['role'].lower() == 'coordinator':
            coordinator_module(user)
        elif user['role'].lower() == 'professor':
            teacher_module(user)
        else:
            st.error("Perfil desconhecido.")

if __name__ == "__main__":
    main()
