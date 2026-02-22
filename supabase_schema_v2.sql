-- ================================================================
-- SGA-H v2.0 — MIGRATION SCRIPT COMPLETO
-- Execute este arquivo inteiro no SQL Editor do Supabase
-- Ordem: ALTER nas tabelas existentes PRIMEIRO, depois CREATE novas
-- ================================================================

-- ================================================================
-- PARTE 1: ALTERAR TABELAS EXISTENTES
-- ================================================================

-- 1a. USERS — adicionar perfil completo e papéis
ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS full_name   TEXT,
    ADD COLUMN IF NOT EXISTS email       TEXT UNIQUE,
    ADD COLUMN IF NOT EXISTS role        TEXT DEFAULT 'teacher'
        CHECK (role IN ('admin', 'coordinator', 'teacher')),
    ADD COLUMN IF NOT EXISTS is_active   BOOLEAN DEFAULT true,
    ADD COLUMN IF NOT EXISTS avatar_url  TEXT;

-- 1b. SETUP_CLASSES — adicionar ano letivo, nível e turno
ALTER TABLE public.setup_classes
    ADD COLUMN IF NOT EXISTS year_level  INTEGER,       -- 6, 7, 8, 9 (Fundamental II)
    ADD COLUMN IF NOT EXISTS school_year INTEGER DEFAULT EXTRACT(YEAR FROM NOW())::INT,
    ADD COLUMN IF NOT EXISTS shift       TEXT DEFAULT 'morning'
        CHECK (shift IN ('morning', 'afternoon', 'evening'));

-- 1c. STUDENTS — dados completos
ALTER TABLE public.students
    ADD COLUMN IF NOT EXISTS birth_date        DATE,
    ADD COLUMN IF NOT EXISTS enrollment_number TEXT UNIQUE,
    ADD COLUMN IF NOT EXISTS status            TEXT DEFAULT 'active'
        CHECK (status IN ('active', 'transferred', 'inactive'));

-- 1d. SETUP_DISCIPLINES — dados completos para UI
ALTER TABLE public.setup_disciplines
    ADD COLUMN IF NOT EXISTS abbreviation TEXT,
    ADD COLUMN IF NOT EXISTS color_code   TEXT DEFAULT '#6366f1',
    ADD COLUMN IF NOT EXISTS area         TEXT;

-- 1e. BNCC_LIBRARY — ano escolar e objeto do conhecimento
ALTER TABLE public.bncc_library
    ADD COLUMN IF NOT EXISTS year_grade           INTEGER, -- 6, 7, 8, 9
    ADD COLUMN IF NOT EXISTS area                 TEXT,
    ADD COLUMN IF NOT EXISTS object_of_knowledge  TEXT;

-- 1f. TEACHER_RUBRICS — status de aprovação e bimestre
-- Nota: esta tabela continuará existindo para compatibilidade
ALTER TABLE public.teacher_rubrics
    ADD COLUMN IF NOT EXISTS discipline_id       INTEGER REFERENCES public.setup_disciplines(id),
    ADD COLUMN IF NOT EXISTS bimester            INTEGER CHECK (bimester BETWEEN 1 AND 4),
    ADD COLUMN IF NOT EXISTS status              TEXT DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    ADD COLUMN IF NOT EXISTS approved_at         TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS objective_explanation TEXT;

-- 1g. ASSESSMENTS — dados de contexto por avaliação
ALTER TABLE public.assessments
    ADD COLUMN IF NOT EXISTS bimester      INTEGER CHECK (bimester BETWEEN 1 AND 4),
    ADD COLUMN IF NOT EXISTS class_name    TEXT,
    ADD COLUMN IF NOT EXISTS discipline_id INTEGER REFERENCES public.setup_disciplines(id),
    ADD COLUMN IF NOT EXISTS teacher_id    UUID REFERENCES public.users(id),
    ADD COLUMN IF NOT EXISTS objective_id  UUID; -- FK para learning_objectives (adicionada depois)

-- ================================================================
-- PARTE 2: CRIAR NOVAS TABELAS
-- ================================================================

-- 2a. COMPETÊNCIAS ESPECÍFICAS POR DISCIPLINA
--     Usadas nos prompts de IA para gerar objetivos contextualizados
CREATE TABLE IF NOT EXISTS public.specific_competencies (
    id               SERIAL PRIMARY KEY,
    discipline_id    INTEGER NOT NULL REFERENCES public.setup_disciplines(id) ON DELETE CASCADE,
    year_grade       INTEGER,                -- NULL = vale para todos os anos
    competency_number INTEGER NOT NULL,
    description      TEXT NOT NULL,
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2b. OBJETIVOS DE APRENDIZAGEM
--     Separados das rubricas; vinculados a uma habilidade BNCC
--     O planejamento é por ANO ESCOLAR + BIMESTRE (todas as turmas do mesmo ano compartilham)
CREATE TABLE IF NOT EXISTS public.learning_objectives (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bncc_code       TEXT NOT NULL REFERENCES public.bncc_library(bncc_code),
    discipline_id   INTEGER REFERENCES public.setup_disciplines(id),
    year_level      INTEGER NOT NULL,           -- Ano escolar (6, 7, 8, 9)
    bimester        INTEGER NOT NULL CHECK (bimester BETWEEN 1 AND 4),
    description     TEXT NOT NULL,
    order_index     INTEGER NOT NULL DEFAULT 1, -- Ordem progressiva (1, 2, 3...)
    ai_explanation  TEXT,                       -- Explicação da IA do porquê deste objetivo
    status          TEXT DEFAULT 'draft'
        CHECK (status IN ('draft', 'pending', 'approved', 'rejected')),
    created_by      UUID REFERENCES public.users(id),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2c. RUBRICAS (4 NÍVEIS POR OBJETIVO)
CREATE TABLE IF NOT EXISTS public.rubric_levels (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    objective_id    UUID NOT NULL REFERENCES public.learning_objectives(id) ON DELETE CASCADE,
    level           INTEGER NOT NULL CHECK (level BETWEEN 1 AND 4),
    description     TEXT NOT NULL,
    status          TEXT DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    created_by      UUID REFERENCES public.users(id),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(objective_id, level)
);

-- 2d. HISTÓRICO DE APROVAÇÕES DOS OBJETIVOS
--     Registra quem aprovou, quem editou, e o conteúdo anterior
CREATE TABLE IF NOT EXISTS public.objective_approvals (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    objective_id         UUID NOT NULL REFERENCES public.learning_objectives(id) ON DELETE CASCADE,
    teacher_id           UUID NOT NULL REFERENCES public.users(id),
    action               TEXT NOT NULL CHECK (action IN ('approved', 'rejected', 'edited')),
    previous_description TEXT,  -- Conteúdo ANTES da edição
    notes                TEXT,
    created_at           TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2e. HISTÓRICO DE APROVAÇÕES DAS RUBRICAS
CREATE TABLE IF NOT EXISTS public.rubric_approvals (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rubric_level_id      UUID NOT NULL REFERENCES public.rubric_levels(id) ON DELETE CASCADE,
    teacher_id           UUID NOT NULL REFERENCES public.users(id),
    action               TEXT NOT NULL CHECK (action IN ('approved', 'rejected', 'edited')),
    previous_description TEXT,
    notes                TEXT,
    created_at           TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2f. VÍNCULO PROFESSOR – TURMA – DISCIPLINA
--     Define quem é professor de qual disciplina em qual turma
CREATE TABLE IF NOT EXISTS public.teacher_class_discipline (
    id            SERIAL PRIMARY KEY,
    teacher_id    UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    class_id      INTEGER NOT NULL REFERENCES public.setup_classes(id) ON DELETE CASCADE,
    discipline_id INTEGER NOT NULL REFERENCES public.setup_disciplines(id) ON DELETE CASCADE,
    school_year   INTEGER DEFAULT EXTRACT(YEAR FROM NOW())::INT,
    UNIQUE(teacher_id, class_id, discipline_id, school_year)
);

-- 2g. PLANEJAMENTO POR ANO ESCOLAR + BIMESTRE
--     Cada habilidade BNCC é associada a 1 bimestre de 1 ano escolar.
--     TODAS as turmas do mesmo ano compartilham o mesmo planejamento.
CREATE TABLE IF NOT EXISTS public.planning_bimester (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bncc_code     TEXT NOT NULL REFERENCES public.bncc_library(bncc_code),
    discipline_id INTEGER NOT NULL REFERENCES public.setup_disciplines(id),
    year_level    INTEGER NOT NULL,          -- Ano escolar: 6, 7, 8, 9
    bimester      INTEGER NOT NULL CHECK (bimester BETWEEN 1 AND 4),
    school_year   INTEGER DEFAULT EXTRACT(YEAR FROM NOW())::INT,
    teacher_id    UUID REFERENCES public.users(id),
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bncc_code, discipline_id, year_level, bimester, school_year)
);

-- ================================================================
-- PARTE 3: FK ADICIONAL (após criar tabelas)
-- ================================================================

-- Adicionar FK de assessments para learning_objectives (safe — verifica antes de criar)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_assessments_objective'
          AND table_name = 'assessments'
    ) THEN
        ALTER TABLE public.assessments
            ADD CONSTRAINT fk_assessments_objective
            FOREIGN KEY (objective_id) REFERENCES public.learning_objectives(id);
    END IF;
END $$;


-- ================================================================
-- PARTE 4: ÍNDICES PARA PERFORMANCE
-- ================================================================
CREATE INDEX IF NOT EXISTS idx_learning_objectives_bncc     ON public.learning_objectives(bncc_code);
CREATE INDEX IF NOT EXISTS idx_learning_objectives_bimester ON public.learning_objectives(bimester, year_level);
CREATE INDEX IF NOT EXISTS idx_learning_objectives_status   ON public.learning_objectives(status);
CREATE INDEX IF NOT EXISTS idx_rubric_levels_objective      ON public.rubric_levels(objective_id);
CREATE INDEX IF NOT EXISTS idx_planning_bimester_year       ON public.planning_bimester(year_level, bimester, discipline_id);
CREATE INDEX IF NOT EXISTS idx_assessments_student          ON public.assessments(student_id);
CREATE INDEX IF NOT EXISTS idx_assessments_bimester         ON public.assessments(bimester, discipline_id);
CREATE INDEX IF NOT EXISTS idx_teacher_class_discipline     ON public.teacher_class_discipline(teacher_id, class_id);
CREATE INDEX IF NOT EXISTS idx_objective_approvals          ON public.objective_approvals(objective_id, teacher_id);
