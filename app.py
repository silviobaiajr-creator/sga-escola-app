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
        st.error(f"Erro ao ler aba '{worksheet_name}': {e}")
        # st.warning(f"Aba '{worksheet_name}' não encontrada ou vazia. Verifique a planilha.")
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
            
            # 5. Correção do ENTER: Usando st.form
            with st.form("login_form"):
                username = st.text_input("Usuário / CPF") # 1. Sugestão de Label
                password = st.text_input("Senha", type="password")
                submit_login = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit_login:
                users_df = get_data("users")
                
                if users_df.empty:
                    st.error("Tabela de usuários não encontrada ou vazia.")
                    return

                # LIMPEZA DE COLUNAS (Remover espaços nos cabeçalhos)
                users_df.columns = users_df.columns.str.strip()

                # Verifica credenciais
                # Função robusta para limpar senhas
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
                setup_df = get_data("setup_classes")
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
                        setup_df = get_data("setup_classes")
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
    # 3. Layout Otimizado: Header compacto
    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown(f"### 🍎 Professor: **{user_info['name']}**")
    with c_head2:
        if st.button("Sair", key="logout_btn_top"):
            st.session_state["logged_in"] = False
            st.rerun()
    
    st.divider() # Linha sutil para separar header
    
    tab1, tab2, tab3 = st.tabs(["📝 Planejamento", "✅ Avaliação", "📊 Relatórios"])
    
    # --- ABA 1: PLANEJAMENTO ---
    with tab1:
        bncc_df = get_data("bncc_library")
        if bncc_df.empty:
            st.warning("Biblioteca BNCC vazia.")
        else:
            # Seleção de Habilidade
            bncc_options = bncc_df['code'] + " - " + bncc_df['description'].str[:30] + "..."
            selected_bncc_str = st.selectbox("Selecione a Habilidade (BNCC)", bncc_options)
            selected_code = selected_bncc_str.split(" - ")[0]
            
            # 7. Exibir Descrição Completa
            full_desc = bncc_df[bncc_df['code'] == selected_code]['description'].values[0]
            st.info(f"📄 **Descrição:** {full_desc}")
            
            with st.form("rubric_form"):
                st.markdown(f"**Defina os critérios para: {selected_code}**")
                c_rub1, c_rub2 = st.columns(2)
                with c_rub1:
                    l1 = st.text_area("Nível 1 (Iniciante)", height=100)
                    l2 = st.text_area("Nível 2 (Básico)", height=100)
                with c_rub2:
                    l3 = st.text_area("Nível 3 (Proficiente)", height=100)
                    l4 = st.text_area("Nível 4 (Avançado)", height=100)
                
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
        # Layout compacto para filtros
        cf1, cf2 = st.columns(2)
        with cf1:
            allowed_classes = [c.strip() for c in str(user_info.get('allowed_classes', '')).split(',')]
            selected_class = st.selectbox("Turma", allowed_classes)
        
        with cf2:
            rubrics_df = get_data("teacher_rubrics")
            my_rubrics = rubrics_df[rubrics_df['teacher_username'] == user_info['username']]
            if my_rubrics.empty:
                st.warning("Sem rubricas.")
                rubric_options = []
            else:
                rubric_options = my_rubrics['bncc_code'].unique()
                selected_skill = st.selectbox("Habilidade", rubric_options)
        
        if not my_rubrics.empty and selected_skill:
             # Visualizar Rubrica Atual (Expander para economizar espaço)
            current_rubric = my_rubrics[my_rubrics['bncc_code'] == selected_skill].iloc[0]
            with st.expander("📖 Ver Guia de Correção (Rubrica)", expanded=False):
                st.markdown(f"""
                | Nível 1 | Nível 2 | Nível 3 | Nível 4 |
                |---|---|---|---|
                | {current_rubric['desc_level_1']} | {current_rubric['desc_level_2']} | {current_rubric['desc_level_3']} | {current_rubric['desc_level_4']} |
                """)

            # Grid de Alunos
            students_df = get_data("students")
            class_students = students_df[students_df['class_name'] == selected_class]
            
            if not class_students.empty:
                with st.form("assessment_form"):
                    st.write(f"Avaliando: **{selected_class}** - **{selected_skill}**")
                    
                    grades = {}
                    
                    # Tabela mais compacta
                    for index, row in class_students.iterrows():
                        c_alu, c_nota = st.columns([2, 3])
                        with c_alu:
                            st.write(f"**{row['student_name']}**")
                            st.caption(f"ID: {row['student_id']}")
                        with c_nota:
                            # 4. Input Otimizado: Radio horizontal
                            grades[row['student_id']] = st.radio(
                                "Nível", 
                                options=["1", "2", "3", "4"],
                                horizontal=True,
                                key=f"grade_{row['student_id']}",
                                label_visibility="collapsed" # Esconde o label "Nível" para limpar visual
                            )
                        st.divider()
                    
                    c_date, c_bim, c_sub = st.columns([1, 1, 1])
                    with c_date:
                        data_ref = st.date_input("Data", datetime.now())
                    with c_bim:
                        bimester = st.selectbox("Bimestre", ["1º", "2º", "3º", "4º"])
                    with c_sub:
                        st.write("") # Espaço
                        st.write("") 
                        submit_grades = st.form_submit_button("💾 Salvar Tudo", use_container_width=True)
                    
                    if submit_grades:
                        # ... (Lógica de salvamento existente) ...
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
                        df_updated = pd.concat([current_assessments, df_new], ignore_index=True)
                        save_data(df_updated, "assessments")

    # --- ABA 3: RELATÓRIOS ---
    with tab3:
        all_assessments = get_data("assessments")
        class_assessments = all_assessments[all_assessments['class_name'].isin(allowed_classes)]
        
        if class_assessments.empty:
            st.info("Sem dados.")
        else:
             # Filtro Global da Aba
            class_filter = st.selectbox("Turma para Análise", allowed_classes, key="rep_class")
            df_turma = class_assessments[class_assessments['class_name'] == class_filter]
            
            # Processar dados
            df_final = calcular_notas(df_turma)
            df_final['level_numeric'] = pd.to_numeric(df_final['level_assigned'], errors='coerce')

            tab_g1, tab_g2 = st.tabs(["🔥 Mapa de Calor", "📈 Evolução"])
            
            with tab_g1:
                # Heatmap existente
                if not df_final.empty:
                    pivot = df_final.pivot_table(index='student_id', columns='bncc_code', values='level_numeric', aggfunc='max')
                    fig_heat = px.imshow(pivot, color_continuous_scale='RdYlGn', zmin=1, zmax=4, text_auto=True, title="Nível Atual por Habilidade")
                    st.plotly_chart(fig_heat, use_container_width=True)
            
            with tab_g2:
                # 2. Evolução Geral (Média da Turma ou Média do Aluno)
                vis_type = st.radio("Visualizar:", ["Individual (Por Habilidade)", "Geral do Aluno (Média Todas Habilidades)"], horizontal=True)
                
                if vis_type == "Individual (Por Habilidade)":
                    # Gráfico existente
                    c_sel1, c_sel2 = st.columns(2)
                    with c_sel1:
                        student_sel = st.selectbox("Aluno", df_turma['student_id'].unique())
                    with c_sel2:
                        skill_sel = st.selectbox("Habilidade", df_turma['bncc_code'].unique())
                    
                    evo_df = df_turma[(df_turma['student_id'] == student_sel) & (df_turma['bncc_code'] == skill_sel)].sort_values('date')
                    if not evo_df.empty:
                        fig = px.line(evo_df, x='date', y=pd.to_numeric(evo_df['level_assigned']), markers=True, title=f"Evolução: {skill_sel}")
                        fig.update_yaxes(range=[0.5, 4.5], tickvals=[1,2,3,4])
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Nenhum histórico encontrado para este aluno nesta habilidade.")
                
                else:
                    # Nova funcionalidade: Média Geral do Aluno ao longo do tempo
                    student_sel_g = st.selectbox("Selecione o Aluno", df_turma['student_id'].unique(), key="st_gen")
                    
                    # Filtrar aluno
                    df_student = df_turma[df_turma['student_id'] == student_sel_g].copy()
                    df_student['date'] = pd.to_datetime(df_student['date'])
                    df_student['level_numeric'] = pd.to_numeric(df_student['level_assigned'])
                    
                    # Agrupar por data (Média de todas as habilidades avaliadas naquele dia/período)
                    # Para ser mais justo, calculamos a média ACUMULADA. Mas simplificado: Média por dia de avaliação.
                    df_grouped = df_student.groupby('date')['level_numeric'].mean().reset_index()
                    
                    if not df_grouped.empty:
                        fig_gen = px.area(df_grouped, x='date', y='level_numeric', title="Evolução Média Geral (Todas Habilidades)", markers=True)
                        fig_gen.update_yaxes(range=[0, 4.5], title="Nível Médio")
                        st.plotly_chart(fig_gen, use_container_width=True)
                        st.caption("Nota: Este gráfico mostra a média dos níveis atribuídos em cada data de avaliação.")
                    else:
                        st.warning("Sem dados suficientes.")


# ==============================================================================
# MAIN APP FLOW
# ==============================================================================

def main():
    if login():
        user = st.session_state["user_info"]
        
        # Sidebar simplificado
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/3413/3413535.png", width=50)
            # 3. Layout: Nome no Sidebar ao invés de Header GIGANTE
            st.write(f"Olá, **{user['name']}**")
            
            if st.button("Sair"):
                st.session_state["logged_in"] = False
                st.rerun()
        
        if user['role'].lower() == 'admin':
            admin_module()
        elif user['role'].lower() == 'professor':
            teacher_module(user)
        else:
            st.error("Perfil desconhecido.")

if __name__ == "__main__":
    main()
