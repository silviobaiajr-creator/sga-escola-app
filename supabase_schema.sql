-- MIGRACAO SGA-H: SCRIPT DE CRIACAO DO BANCO DE DADOS (SUPABASE)
-- Execute este script no SQL Editor do seu projeto Supabase.

-- 1. Tabela: setup_classes (Turmas)
CREATE TABLE public.setup_classes (
    id SERIAL PRIMARY KEY,
    class_name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Tabela: users (Usuários / Professores)
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    must_change_password BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Tabela: students (Alunos)
CREATE TABLE public.students (
    student_id TEXT PRIMARY KEY,
    student_name TEXT NOT NULL,
    class_name TEXT NOT NULL REFERENCES public.setup_classes(class_name) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Tabela: setup_disciplines (Disciplinas)
CREATE TABLE public.setup_disciplines (
    id SERIAL PRIMARY KEY,
    discipline_name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Tabela: bncc_library (Habilidades BNCC)
CREATE TABLE public.bncc_library (
    bncc_code TEXT PRIMARY KEY,
    skill_description TEXT NOT NULL,
    discipline_id INTEGER REFERENCES public.setup_disciplines(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. Tabela: teacher_rubrics (Rubricas Criadas por IA ou Manualmente)
CREATE TABLE public.teacher_rubrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rubric_id TEXT UNIQUE NOT NULL,
    bncc_code TEXT NOT NULL,
    objective TEXT NOT NULL,
    level_1_desc TEXT,
    level_2_desc TEXT,
    level_3_desc TEXT,
    level_4_desc TEXT,
    created_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 7. Tabela: assessments (Avaliações / Notas)
CREATE TABLE public.assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id TEXT NOT NULL REFERENCES public.students(student_id) ON DELETE CASCADE,
    rubric_id TEXT NOT NULL REFERENCES public.teacher_rubrics(rubric_id) ON DELETE CASCADE,
    bncc_code TEXT NOT NULL,
    level_assigned INTEGER CHECK (level_assigned >= 1 AND level_assigned <= 4),
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Permissões Iniciais (RLS)
-- Inicialmente, vamos deixar desativado ou permitir acesso completo para facilitar o desenvolvimento (já que o app atual nao tem tenants complexos)
-- Depois podemos fechar a segurança com Row Level Security
