import pandas as pd
import random
import datetime

def generate_mock_data():
    """
    Gera dados fictícios para teste de carga e validação dos gráficos.
    Retorna 4 DataFrames: classes, students, rubrics, assessments
    """
    # 1. Configurações
    num_classes = 5
    students_per_class = 30
    skills_per_disc = 8
    objs_per_skill = 2
    
    disciplines = ["MATEMATICA", "PORTUGUES", "HISTORIA", "GEOGRAFIA", "CIENCIAS"]
    grades = ["6º Ano A", "7º Ano B", "8º Ano C", "9º Ano D", "9º Ano E"] # 5 Turmas
    
    # 2. Gerar Turmas (setup_classes)
    # Formato esperado: class_name, grade, shift
    cols_classes = ["class_name", "grade", "shift"]
    data_classes = []
    for g in grades:
        data_classes.append({
            "class_name": g,
            "grade": g.split(" ")[0] + " Ano", # Ex: 6º Ano
            "shift": "Matutino"
        })
    df_classes = pd.DataFrame(data_classes, columns=cols_classes)

    # 3. Gerar Alunos (students)
    # Formato: student_id, student_name, class_name
    first_names = ["Ana", "Bruno", "Carlos", "Daniela", "Eduardo", "Fernanda", "Gabriel", "Helena", "Igor", "Julia", 
                   "Lucas", "Mariana", "Nicolas", "Olivia", "Pedro", "Rafaela", "Samuel", "Tatiana", "Vinicius", "Yasmin",
                   "Arthur", "Beatriz", "Caio", "Diana", "Enzo", "Flavia", "Gustavo", "Heitor", "Isabela", "Joao"]
    last_names = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes"]
    
    data_students = []
    student_id_counter = 1000
    
    for cls in grades:
        for i in range(students_per_class):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            full_name = f"{fname} {lname} {cls.split(' ')[0]}" # Sulfixo para garantir unicidade visual
            
            data_students.append({
                "student_id": str(student_id_counter),
                "student_name": full_name,
                "class_name": cls
            })
            student_id_counter += 1
            
    df_students = pd.DataFrame(data_students)

    # 4. Gerar Rubricas (teacher_rubrics)
    # Formato: rubric_id, teacher_username, bncc_code, objective, discipline_id, desc_level_1...4, status
    data_rubrics = []
    
    # Para garantir consistência, vamos criar um mapa de Habilidades -> Objetivos
    # Estrutura: { discipline: [ {code: 'EF01', objs: [obj1, obj2]} ] }
    map_skills = {} 
    
    for disc in disciplines:
        map_skills[disc] = []
        for s in range(1, skills_per_disc + 1):
            # Código BNCC Fictício: EF + Disc + Num
            # Ex: EF06MA01
            code_num = f"{s:02d}"
            disc_sigla = disc[:2] # MA, PO, HI...
            bncc_code = f"EF0{random.randint(6,9)}{disc_sigla}{code_num}"
            
            objs_list = []
            for o in range(1, objs_per_skill + 1):
                obj_text = f"Analisar e compreender o conceito {o} da habilidade {bncc_code} em {disc}."
                rubric_id = f"MOCK_{bncc_code}_{o}"
                
                data_rubrics.append({
                    "rubric_id": rubric_id,
                    "teacher_username": "mock_admin",
                    "bncc_code": bncc_code,
                    "objective": obj_text,
                    "discipline_id": disc,
                    "desc_level_1": "Não atingiu o básico (Simulado)",
                    "desc_level_2": "Atingiu parcialmente (Simulado)",
                    "desc_level_3": "Atingiu o esperado (Simulado)",
                    "desc_level_4": "Superou expectativas (Simulado)",
                    "status": "APPROVED",
                    "approvals": "mock_admin"
                })
                objs_list.append(rubric_id)
            
            map_skills[disc].append({"code": bncc_code, "rubric_ids": objs_list})

    df_rubrics = pd.DataFrame(data_rubrics)

    # 5. Gerar Avaliações (assessments) - A PARTE PESADA
    # 100% de cobertura: Todos alunos x Todas disciplinas x Todas Habilidades x Todos Objetivos
    # Variar notas e datas para ter gráficos bonitos
    
    data_assessments = []
    
    start_date = datetime.date(2025, 2, 1)
    end_date = datetime.date(2025, 11, 30)
    days_range = (end_date - start_date).days
    
    # Pré-computar alunos por turma para agilizar
    students_by_class = df_students.groupby('class_name')['student_id'].apply(list).to_dict()
    
    for disc in disciplines:
        # Recuperar habilidades e rubricas desta disciplina
        skills_data = map_skills[disc] # Lista de dicts {code, rubric_ids}
        
        for cls in grades:
            class_students = students_by_class.get(cls, [])
            
            for student_id in class_students:
                # Perfil de desempenho do aluno (Aleatório para variar)
                # 0: Fraco, 1: Médio, 2: Bom
                perf_profile = random.choices([0, 1, 2], weights=[0.2, 0.5, 0.3])[0]
                
                for skill in skills_data:
                    skill_code = skill['code']
                    rubric_ids = skill['rubric_ids']
                    
                    for r_id in rubric_ids:
                        # Gerar Nota baseada no perfil
                        if perf_profile == 0: # Fraco
                            nota = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
                        elif perf_profile == 1: # Médio
                            nota = random.choices([2, 3, 4], weights=[0.2, 0.6, 0.2])[0]
                        else: # Bom
                            nota = random.choices([3, 4], weights=[0.4, 0.6])[0]
                        
                        # Data aleatória
                        rand_days = random.randint(0, days_range)
                        date_eval = start_date + datetime.timedelta(days=rand_days)
                        
                        # Bimestre aproximado pela data
                        month = date_eval.month
                        if month <= 4: bim = "1º"
                        elif month <= 7: bim = "2º"
                        elif month <= 9: bim = "3º"
                        else: bim = "4º"
                        
                        data_assessments.append({
                            "timestamp": datetime.datetime.now().isoformat(),
                            "date": date_eval.isoformat(),
                            "bimester_ref": bim,
                            "grade_ref": cls.split(" ")[0] + " Ano",
                            "teacher": "mock_teacher",
                            "discipline": disc,
                            "class_name": cls,
                            "student_id": student_id,
                            "bncc_code": skill_code,
                            "rubric_id": r_id,
                            "level_assigned": nota
                        })
    
    df_assessments = pd.DataFrame(data_assessments)
    
    return df_classes, df_students, df_rubrics, df_assessments
