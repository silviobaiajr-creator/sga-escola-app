import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account
import json
import os
import re
from typing import List, Optional

CANDIDATE_MODELS = [
    "gemini-2.0-flash-001",
    "gemini-1.5-flash-001",
    "gemini-2.5-flash",
]

def init_vertex_ai():
    """Inicializa o Vertex AI.
    Prioridade:
    1. Application Default Credentials (ADC) — funciona nativamente no Cloud Run.
    2. Arquivo local .streamlit/gcp_key.json — para desenvolvimento local.
    3. Variável de ambiente GCP_SERVICE_ACCOUNT — fallback para outros hosts.
    """
    project_id = os.getenv("GCP_PROJECT_ID", "escola-sga")
    location   = os.getenv("GCP_LOCATION", "us-central1")

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
        pass

    for path in [".streamlit/gcp_key.json", "../.streamlit/gcp_key.json"]:
        if os.path.exists(path):
            credentials = service_account.Credentials.from_service_account_file(path)
            vertexai.init(project=project_id, location=location, credentials=credentials)
            return True, "Vertex AI via arquivo gcp_key.json (local)"

    info_str = os.getenv("GCP_SERVICE_ACCOUNT")
    if info_str:
        info_dict = json.loads(info_str)
        credentials = service_account.Credentials.from_service_account_info(info_dict)
        vertexai.init(project=info_dict.get("project_id", project_id), location=location, credentials=credentials)
        return True, "Vertex AI via GCP_SERVICE_ACCOUNT env var"

    return False, "Nenhuma credencial GCP encontrada."


def safe_generate_content(prompt: str) -> str:
    last_error = None
    for model_name in CANDIDATE_MODELS:
        try:
            model    = GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            last_error = e
            print(f"[ai_service] Tentativa falhou com {model_name}: {e}")
            continue
    raise last_error


def generate_objectives(
    skill_code: str,
    skill_description: str,
    quantity: int = 3,
    discipline_name: str = None,
    specific_competencies: Optional[List[str]] = None,
    bimester: Optional[int] = None,
    year_level: Optional[int] = None
) -> dict:
    """
    Gera objetivos de aprendizagem em ordem progressiva.
    Inclui as competências específicas da disciplina no prompt.
    Retorna: { objectives: [...], explanations: [...], explanation: str }
    """
    success, msg = init_vertex_ai()
    if not success:
        return {"error": msg}

    # Formatar competências específicas para o prompt
    comp_section = ""
    if specific_competencies:
        comp_list = "\n".join([f"  {c}" for c in specific_competencies])
        comp_section = f"""
3. COMPETÊNCIAS ESPECÍFICAS DA DISCIPLINA (contexto obrigatório):
{comp_list}
"""

    bimester_info = f"Bimestre: {bimester}º" if bimester else ""
    year_info     = f"Ano Escolar: {year_level}º ano" if year_level else ""

    prompt = f"""
Você é um **Consultor Pedagógico Sênior**.

1. CONTEXTO DA HABILIDADE:
   BNCC: {skill_code} - {skill_description}
   Disciplina: {discipline_name or 'Geral'}
   {year_info}
   {bimester_info}
{comp_section}
2. SUA TAREFA: Gere EXATAMENTE {quantity} Objetivos de Aprendizagem em ORDEM PROGRESSIVA.
   - REGRA DE OURO 1: GERE EXATAMENTE {quantity} OBJETIVOS. NEM A MAIS, NEM A MENOS.
   - REGRA DE OURO 2: Gere os objetivos em ORDEM PROGRESSIVA rigorosa, onde o primeiro é pré-requisito/base para o segundo e assim por diante.
   - REGRA DE OURO 3: Se houver competências adicionais fornecidas, você DEVE conectar os objetivos a elas, demonstrando o raciocínio.
   - REGRA 4: Comece com verbos da Taxonomia de Bloom (identificar, analisar...).
   - REGRA 5: MÁXIMO 18 palavras por objetivo (seja prático e direto ao ponto).

3. FORMATO DE SAÍDA OBRIGATÓRIO (PARA ECONOMIZAR TOKENS):
EXPLICACAO: [Resuma a integração com as competências e motivo da progressão de forma EXTREMAMENTE CURTA. Máximo de 2 ou 3 frases. Seja objetivo.]
###
OBJ1: [texto 1]|[justificativa super curta 1]
OBJ2: [texto 2]|[justificativa super curta 2]
...
OBJ{quantity}: [texto {quantity}]|[justificativa super curta {quantity}]
"""

    try:
        text = safe_generate_content(prompt)

        explanation = ""
        objectives  = []
        explanations = []

        if "###" in text:
            parts   = text.split("###", 1)
            explanation = parts[0].replace("EXPLICACAO:", "").replace("EXPLICAÇÃO:", "").strip()
            obj_block   = parts[1].strip()
        else:
            obj_block   = text
            explanation = "A IA gerou os objetivos diretamente."

        # Parsear cada linha OBJx
        for line in obj_block.split("\n"):
            clean = line.strip()
            # Tentar formato OBJ1: xxx|yyy
            match = re.match(r"^OBJ\d+:\s*(.+)$", clean, re.IGNORECASE)
            if match:
                content = match.group(1)
                if "|" in content:
                    obj_text, obj_exp = content.split("|", 1)
                    objectives.append(obj_text.strip())
                    explanations.append(obj_exp.strip())
                else:
                    objectives.append(content.strip())
                    explanations.append("")
            elif clean and not clean.startswith("#") and len(clean) > 5:
                # Fallback: linha simples
                cleaned = re.sub(r"^[-*•\d.]+\s*", "", clean).strip()
                if cleaned and not re.match(r"^(EXPLICACAO|EXPLICAÇÃO|##)", cleaned, re.IGNORECASE):
                    objectives.append(cleaned)
                    explanations.append("")

        return {
            "objectives":   objectives[:quantity],
            "explanations": explanations[:quantity],
            "explanation":  explanation,
        }

    except Exception as e:
        return {"error": str(e)}


def generate_rubric(skill_code: str, objective: str) -> dict:
    """Gera os 4 níveis da rubrica para um objetivo."""
    success, msg = init_vertex_ai()
    if not success:
        return {"error": msg}

    prompt = f"""
Você é um Especialista em Avaliação por Rubrica (BNCC).

Objetivo de Aprendizagem: {objective}
Habilidade BNCC Original: {skill_code}

Tarefa: Crie uma rubrica de avaliação com 4 níveis para avaliar o desempenho do aluno
neste objetivo. Os descritores devem ser claros, observáveis e em linguagem simples
para que o professor possa identificar facilmente o nível do aluno em sala de aula.

Nível 1 — Iniciante: ainda não demonstra a habilidade.
Nível 2 — Em Desenvolvimento: demonstra parcialmente, com muita ajuda.
Nível 3 — Proficiente: demonstra a habilidade de forma autônoma.
Nível 4 — Avançado: demonstra a habilidade e a aprofunda/aplica em novos contextos.

FORMATO OBRIGATÓRIO (texto puro):
N1: Descrição nível 1...
N2: Descrição nível 2...
N3: Descrição nível 3...
N4: Descrição nível 4...
"""

    try:
        text  = safe_generate_content(prompt)
        rubric = {}
        for line in text.split("\n"):
            clean = line.strip()
            for level in ["1", "2", "3", "4"]:
                if clean.startswith(f"N{level}:"):
                    rubric[level] = clean.replace(f"N{level}:", "").strip()
        return {"rubric": rubric}
    except Exception as e:
        return {"error": str(e)}
