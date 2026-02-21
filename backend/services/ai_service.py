import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account
from sqlalchemy.orm import Session
from backend.models import SetupDiscipline
import json
import os
import re

CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-001",
    "gemini-2.5-pro",
    "gemini-1.5-flash-001"
]

def init_vertex_ai():
    """Inicializa o Vertex AI.
    Prioridade:
    1. Application Default Credentials (ADC) — funciona nativamente no Cloud Run.
    2. Arquivo local .streamlit/gcp_key.json — para desenvolvimento local.
    3. Variável de ambiente GCP_SERVICE_ACCOUNT — fallback para outros hosts.
    """
    project_id = os.getenv("GCP_PROJECT_ID", "escola-sga")
    location = os.getenv("GCP_LOCATION", "us-central1")

    # 1. ADC — Cloud Run usa o service account do projeto automaticamente
    try:
        import google.auth
        credentials, detected_project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        vertexai.init(
            project=detected_project or project_id,
            location=location,
            credentials=credentials
        )
        return True, f"Vertex AI via ADC (projeto: {detected_project or project_id})"
    except Exception:
        pass  # ADC não disponível, tenta próxima opção

    # 2. Arquivo local de chave (dev local)
    for path in [".streamlit/gcp_key.json", "../.streamlit/gcp_key.json"]:
        if os.path.exists(path):
            credentials = service_account.Credentials.from_service_account_file(path)
            vertexai.init(project=project_id, location=location, credentials=credentials)
            return True, "Vertex AI via arquivo gcp_key.json (local)"

    # 3. Variável de ambiente (outros hosts como Render)
    info_str = os.getenv("GCP_SERVICE_ACCOUNT")
    if info_str:
        info_dict = json.loads(info_str)
        credentials = service_account.Credentials.from_service_account_info(info_dict)
        vertexai.init(project=info_dict.get("project_id", project_id), location=location, credentials=credentials)
        return True, "Vertex AI via GCP_SERVICE_ACCOUNT env var"

    return False, "Nenhuma credencial GCP encontrada. Configure ADC, gcp_key.json ou GCP_SERVICE_ACCOUNT."

def safe_generate_content(prompt):
    last_error = None
    for model_name in CANDIDATE_MODELS:
        try:
            model = GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            last_error = e
            print(f"Tentativa falhou no backend com {model_name}: {e}")
            continue
    raise last_error

def generate_objectives(skill_code: str, skill_description: str, quantity: int = 3, discipline_name: str = None) -> dict:
    success, msg = init_vertex_ai()
    if not success:
        return {"error": msg}
    
    # Obs: na API no futuro conectaremos ao BD ou deixamos sem usar o Sheets
    # Para simplificar na API Python, enviaremos apenas pela habilidade ou passaremos o contexto manual
    
    prompt = f"""
    Atue como um Especialista Pedagógico (Sub-Chef) Sênior.
    
    1. ANALISE O CONTEXTO (Habilidade BNCC):
    Habilidade: {skill_code} - {skill_description}
    Disciplina: {discipline_name or 'Geral'}
    
    2. TAREFA - Gere DUAS saídas:
    
    [PARTE A] EXPLICAÇÃO PEDAGÓGICA (Breve):
    - Explique em 1 parágrafo como os objetivos cobrem toda a habilidade progressivamente.
    
    [PARTE B] OBJETIVOS DE AULA (Lista):
    - Crie {quantity} objetivos práticos e diretos.
    - O primeiro objetivo deve introduzir o tema e o último deve consolidar a habilidade completa.
    - NÃO use frases introdutórias. Comece direto com o verbo da Taxonomia de Bloom.
    - SEJA EXTREMAMENTE OBJETIVO. MÁXIMO 15 palavras por objetivo.
    
    FORMATO DE SAÍDA OBRIGATÓRIO (Use o separador "###"):
    EXPLICAÇÃO: [Sua explicação aqui]
    ###
    OBJETIVO 1
    OBJETIVO 2
    OBJETIVO 3
    ...
    """
    
    try:
        text = safe_generate_content(prompt)
        
        explanation = "Explicação não gerada."
        objectives_raw = ""
        
        if "###" in text:
            parts = text.split("###")
            explanation = parts[0].replace("EXPLICAÇÃO:", "").strip()
            objectives_raw = parts[1].strip()
        else:
            objectives_raw = text
            explanation = "A IA gerou os objetivos diretamente."

        lines = []
        for line in objectives_raw.split('\n'):
            cleaned = line.strip().lstrip('-').lstrip('*').lstrip('1.').lstrip('2.').lstrip('3.').lstrip('4.').lstrip('5.').strip()
            is_label = re.match(r'^OBJETIVO\s*\d+[:.]*$', cleaned, re.IGNORECASE)
            
            if cleaned and not cleaned.endswith(':') and not is_label: 
                lines.append(cleaned)
        
        return {
            "objectives": lines[:quantity],
            "explanation": explanation
        }
        
    except Exception as e:
        return {"error": str(e)}

def generate_rubric(skill_code: str, objective: str) -> dict:
    success, msg = init_vertex_ai()
    if not success:
        return {"error": msg}
        
    prompt = f"""
    Atue como um Especialista em Avaliação.
    Objetivo da Aula: {objective}
    Habilidade Original: {skill_code}
    
    Tarefa: Crie uma régua de avaliação (rubrica) de 4 níveis para este objetivo específico.
    Nível 1 (Iniciante)
    Nível 2 (Básico)
    Nível 3 (Proficiente)
    Nível 4 (Avançado)
    
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
            if clean_line.startswith("N1:"): rubric["1"] = clean_line.replace("N1:", "").strip()
            elif clean_line.startswith("N2:"): rubric["2"] = clean_line.replace("N2:", "").strip()
            elif clean_line.startswith("N3:"): rubric["3"] = clean_line.replace("N3:", "").strip()
            elif clean_line.startswith("N4:"): rubric["4"] = clean_line.replace("N4:", "").strip()
            
        return {"rubric": rubric}
    except Exception as e:
        return {"error": str(e)}
