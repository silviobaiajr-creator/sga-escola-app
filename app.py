import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==============================================================================
st.set_page_config(
    page_title="SGA-H | Sistema de Gestão de Aprendizagem por Habilidades",
    page_icon="🎓",
    layout="wide"
)

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
    "teacher_rubrics", "assessments"
]

# Função para carregar dados (com cache manual para performance se necessário, mas aqui usando direto)
def get_data(worksheet_name):
    """Carrega dados de uma aba específica."""
    try:
        # ttl=0 força a leitura do Google Sheets para garantir dados atualizados
        df = conn.read(worksheet=worksheet_name, ttl=0)
        return df
    except Exception as e:
        # Se a aba não existir, tenta criar (embora o correto seja o admin criar a planilha base)
        # Aqui vamos apenas retornar vazio ou erro amigável
        st.warning(f"Aba '{worksheet_name}' não encontrada ou vazia. Verifique a planilha.")
        # Retorna DataFrame vazio com colunas esperadas para evitar crash
        return pd.DataFrame()

def save_data(df, worksheet_name):
    """Salva/Sobrescreve dados em uma aba específica."""
    try:
        conn.update(worksheet=worksheet_name, data=df)
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

def login():
    """Sistema simples de login."""
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["user_info"] = None

    if not st.session_state["logged_in"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<h1 style='text-align: center;'>🔐 Login SGA-H</h1>", unsafe_allow_html=True)
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            
            if st.button("Entrar", use_container_width=True):
                users_df = get_data("users")
                
                if users_df.empty:
                    st.error("Tabela de usuários não encontrada ou vazia.")
                    return

                # Verifica credenciais
                user = users_df[
                    (users_df["username"] == username) & 
                    (users_df["password"] == password)
                ]

                if not user.empty:
                    st.session_state["logged_in"] = True
                    st.session_state["user_info"] = user.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
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
    
    # Remover duplicatas mantendo a primeira (que é a mais recente)
    # Chave única: Aluno + Código BNCC
    df_final = df_sorted.drop_duplicates(subset=['student_id', 'bncc_code'], keep='first')
    
    return df_final

def converter_nivel_nota(nivel):
    """Converte nível (1-4) para nota (0-10)."""
    mapping = {1: 2.5, 2: 5.0, 3: 7.5, 4: 10.0}
    try:
        return mapping.get(int(nivel), 0.0)
    except:
        return 0.0

# ==============================================================================
# MÓDULOS DO SISTEMA
# ==============================================================================

def admin_module():
    st.title("🛠️ Painel do Administrador")
    
    tab1, tab2 = st.tabs(["📤 Upload de Alunos", "📊 Dashboards Analíticos"])
    
    # --- ABA 1: UPLOAD DE ALUNOS ---
    with tab1:
        st.subheader("Cadastro em Lote de Alunos")
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
                    setup_df = get_data("setup_classes")
                    if setup_df.empty:
                        st.error("Aba 'setup_classes' está vazia! Configure as turmas antes de importar alunos.")
                        return

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

    # --- ABA 2: DASHBOARDS ANALÍTICOS ---
    with tab2:
        st.subheader("Visão Geral da Escola")
        
        assessments_df = get_data("assessments")
        if assessments_df.empty:
            st.info("Ainda não há avaliações registradas.")
        else:
            # Aplicar Regra de Negócio: Calcular situação atual
            df_atual = calcular_notas(assessments_df)
            
            # Conversão para Nota Numérica
            df_atual['Nota'] = df_atual['level_assigned'].apply(converter_nivel_nota)
            
            st.markdown("### 📈 Conversão de Níveis em Notas (0-10)")
            st.dataframe(df_atual[['class_name', 'student_id', 'bncc_code', 'level_assigned', 'Nota']])
            
            # Alerta de Risco
            st.markdown("### 🚨 Alerta de Risco Pedagógico")
            # Filtrar alunos com Nível 1
            risk_df = df_atual[df_atual['level_assigned'].astype(str) == '1']
            
            # Contar quantas habilidades com nível 1 cada aluno tem
            risk_count = risk_df.groupby(['class_name', 'student_id']).size().reset_index(name='count_level_1')
            
            # Filtrar quem tem mais de 3
            high_risk = risk_count[risk_count['count_level_1'] > 3]
            
            if high_risk.empty:
                st.success("Nenhum aluno em situação de alto risco (> 3 habilidades no nível 1).")
            else:
                st.error(f"Atenção: {len(high_risk)} alunos com dificuldades críticas.")
                st.dataframe(high_risk)


def teacher_module(user_info):
    st.title(f"🍎 Área do Professor: {user_info['name']}")
    
    tab1, tab2, tab3 = st.tabs(["📝 Planejamento (Rubricas)", "✅ Avaliação Contínua", "📊 Relatórios Turma"])
    
    # --- ABA 1: PLANEJAMENTO ---
    with tab1:
        st.subheader("Cadastro de Rubricas de Avaliação")
        
        bncc_df = get_data("bncc_library")
        if bncc_df.empty:
            st.warning("Biblioteca BNCC vazia.")
        else:
            # Seleção de Habilidade
            bncc_options = bncc_df['code'] + " - " + bncc_df['description'].str[:50] + "..."
            selected_bncc_str = st.selectbox("Selecione a Habilidade (BNCC)", bncc_options)
            selected_code = selected_bncc_str.split(" - ")[0]
            
            with st.form("rubric_form"):
                st.markdown(f"**Defina os critérios para: {selected_code}**")
                l1 = st.text_area("Nível 1 (Iniciante)", placeholder="O aluno não consegue...")
                l2 = st.text_area("Nível 2 (Básico)", placeholder="O aluno consegue parcialmente...")
                l3 = st.text_area("Nível 3 (Proficiente)", placeholder="O aluno realiza com autonomia...")
                l4 = st.text_area("Nível 4 (Avançado)", placeholder="O aluno domina e conecta...")
                
                submitted = st.form_submit_button("Salvar Rubrica")
                if submitted:
                    new_rubric = pd.DataFrame([{
                        "rubric_id": f"{user_info['username']}_{selected_code}",
                        "teacher_username": user_info['username'],
                        "bncc_code": selected_code,
                        "desc_level_1": l1,
                        "desc_level_2": l2,
                        "desc_level_3": l3,
                        "desc_level_4": l4
                    }])
                    
                    current_rubrics = get_data("teacher_rubrics")
                    updated_rubrics = pd.concat([current_rubrics, new_rubric], ignore_index=True)
                    # O ideal seria remover duplicatas do mesmo professor+habilidade antes de salvar
                    updated_rubrics.drop_duplicates(subset=['teacher_username', 'bncc_code'], keep='last', inplace=True)
                    
                    save_data(updated_rubrics, "teacher_rubrics")

    # --- ABA 2: AVALIAÇÃO CONTÍNUA ---
    with tab2:
        st.subheader("Lançamento de Avaliações")
        
        # 4.B. Seletores Filtados
        allowed_classes = [c.strip() for c in str(user_info.get('allowed_classes', '')).split(',')]
        selected_class = st.selectbox("Selecione a Turma", allowed_classes)
        
        # Filtrar rubricas do professor
        rubrics_df = get_data("teacher_rubrics")
        my_rubrics = rubrics_df[rubrics_df['teacher_username'] == user_info['username']]
        
        if my_rubrics.empty:
            st.info("Você ainda não cadastrou rubricas. Vá para a aba Planejamento.")
        else:
            rubric_options = my_rubrics['bncc_code'].unique()
            selected_skill = st.selectbox("Habilidade para Avaliar", rubric_options)
            
            # Visualizar Rubrica Atual
            current_rubric = my_rubrics[my_rubrics['bncc_code'] == selected_skill].iloc[0]
            st.info(
                f"**Guia de Correção:**\n\n"
                f"1️⃣ {current_rubric['desc_level_1']}\n\n"
                f"2️⃣ {current_rubric['desc_level_2']}\n\n"
                f"3️⃣ {current_rubric['desc_level_3']}\n\n"
                f"4️⃣ {current_rubric['desc_level_4']}"
            )
            
            # Grid de Alunos
            students_df = get_data("students")
            class_students = students_df[students_df['class_name'] == selected_class]
            
            if class_students.empty:
                st.warning(f"Nenhum aluno encontrado na turma {selected_class}.")
            else:
                with st.form("assessment_form"):
                    st.write(f"Avaliando turma **{selected_class}** em **{selected_skill}**")
                    
                    # Dicionário para guardar as notas
                    grades = {}
                    
                    # Iterar alunos
                    for index, row in class_students.iterrows():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"👤 {row['student_name']} ({row['student_id']})")
                        with col2:
                            grades[row['student_id']] = st.select_slider(
                                "Nível", 
                                options=["1", "2", "3", "4"], 
                                key=f"grade_{row['student_id']}"
                            )
                        st.divider()
                    
                    data_ref = st.date_input("Data da Avaliação", datetime.now())
                    bimester = st.selectbox("Bimestre", ["1º", "2º", "3º", "4º"])
                    
                    submit_grades = st.form_submit_button("💾 Salvar Avaliações")
                    
                    if submit_grades:
                        new_assessments = []
                        timestamp = datetime.now().isoformat()
                        
                        for student_id, level in grades.items():
                            new_assessments.append({
                                "timestamp": timestamp,
                                "date": data_ref,
                                "bimester_ref": bimester,
                                "teacher": user_info['username'],
                                "class_name": selected_class,
                                "student_id": student_id,
                                "bncc_code": selected_skill,
                                "level_assigned": level
                            })
                        
                        df_new = pd.DataFrame(new_assessments)
                        current_assessments = get_data("assessments")
                        
                        # 4.B. Lógica de Salvamento (APPEND)
                        df_updated = pd.concat([current_assessments, df_new], ignore_index=True)
                        save_data(df_updated, "assessments")

    # --- ABA 3: RELATÓRIOS (BI EDUCACIONAL) ---
    with tab3:
        st.subheader("Inteligência de Dados")
        
        all_assessments = get_data("assessments")
        # Filtrar apenas dados desta turma (para simplificar visualização)
        class_assessments = all_assessments[all_assessments['class_name'].isin(allowed_classes)]
        
        if class_assessments.empty:
            st.info("Sem dados suficientes para gráficos.")
        else:
            # Heatmap da Turma
            st.markdown("### 🔥 Mapa de Calor da Turma")
            class_filter = st.selectbox("Filtrar Turma para Heatmap", allowed_classes, key="heatmap_class")
            
            heatmap_data = class_assessments[class_assessments['class_name'] == class_filter]
            
            # Pegar situação mais recente
            heatmap_data = calcular_notas(heatmap_data)
            
            if not heatmap_data.empty:
                # Pivot: Index=Aluno, Columns=Habilidade, Values=Nível
                # Precisamos garantir que Nível seja numérico
                heatmap_data['level_numeric'] = pd.to_numeric(heatmap_data['level_assigned'], errors='coerce')
                
                pivot = heatmap_data.pivot_table(
                    index='student_id', 
                    columns='bncc_code', 
                    values='level_numeric',
                    aggfunc='max' # Só para garantir unicidade, já tratada antes
                )
                
                fig_heat = px.imshow(
                    pivot, 
                    color_continuous_scale=['red', 'orange', 'yellow', 'green'],
                    zmin=1, zmax=4,
                    text_auto=True,
                    aspect="auto",
                    title=f"Desempenho por Habilidade - {class_filter}"
                )
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.warning("Sem dados processados para esta turma.")
            
            # Gráfico de Evolução Individual
            st.markdown("### 📈 Evolução Individual")
            
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                student_sel = st.selectbox("Aluno", class_assessments['student_id'].unique())
            with col_sel2:
                skill_sel = st.selectbox("Habilidade", class_assessments['bncc_code'].unique())
            
            evolution_df = class_assessments[
                (class_assessments['student_id'] == student_sel) & 
                (class_assessments['bncc_code'] == skill_sel)
            ].copy()
            
            if not evolution_df.empty:
                evolution_df['date'] = pd.to_datetime(evolution_df['date'])
                evolution_df['level_numeric'] = pd.to_numeric(evolution_df['level_assigned'])
                evolution_df = evolution_df.sort_values(by='date')
                
                fig_line = px.line(
                    evolution_df, 
                    x='date', 
                    y='level_numeric', 
                    markers=True,
                    range_y=[0.5, 4.5],
                    title=f"Trajetória de Aprendizagem: {student_sel}"
                )
                fig_line.update_yaxes(tickvals=[1, 2, 3, 4], ticktext=["1-Iniciante", "2-Básico", "3-Proficiente", "4-Avançado"])
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("Nenhum histórico encontrado para este aluno nesta habilidade.")


# ==============================================================================
# MAIN APP FLOW
# ==============================================================================

def main():
    if login():
        user = st.session_state["user_info"]
        
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=100)
            st.title(f"Olá, {user['name']}")
            st.write(f"Perfil: **{user['role']}**")
            
            if st.button("Sair"):
                st.session_state["logged_in"] = False
                st.rerun()
        
        if user['role'].lower() == 'admin':
            admin_module()
        elif user['role'].lower() == 'professor':
            teacher_module(user)
        else:
            st.error("Perfil de usuário desconhecido.")

if __name__ == "__main__":
    main()
