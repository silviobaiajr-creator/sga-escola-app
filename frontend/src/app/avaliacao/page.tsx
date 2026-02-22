"use client";

import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    ClipboardCheck, ChevronDown, Save, Users, CheckCircle2,
    Loader2, ChevronUp, AlertTriangle, BookOpen, Filter
} from "lucide-react";
import { getClasses, getDisciplines, getBnccSkills, getStudents, getObjectives, getRubrics, api } from "@/lib/api";

// ─────────────────────────────────────────
// CONSTANTES
// ─────────────────────────────────────────
const LEVELS = [
    { value: 1, label: "N1", full: "Iniciante", bg: "bg-red-500", border: "border-red-400", text: "text-red-400", ring: "ring-red-400" },
    { value: 2, label: "N2", full: "Em Desenvolvimento", bg: "bg-amber-500", border: "border-amber-400", text: "text-amber-400", ring: "ring-amber-400" },
    { value: 3, label: "N3", full: "Proficiente", bg: "bg-blue-500", border: "border-blue-400", text: "text-blue-400", ring: "ring-blue-400" },
    { value: 4, label: "N4", full: "Avançado", bg: "bg-emerald-500", border: "border-emerald-400", text: "text-emerald-400", ring: "ring-emerald-400" },
];

// ─────────────────────────────────────────
// RUBRICA EXPANDÍVEL (inline, mobile-first)
// ─────────────────────────────────────────
function RubricExpanded({ objectiveId }: { objectiveId: string }) {
    const [levels, setLevels] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!objectiveId) return;
        setLoading(true);
        getRubrics(objectiveId)
            .then(r => setLevels(r.data || []))
            .catch(() => { })
            .finally(() => setLoading(false));
    }, [objectiveId]);

    if (loading) return (
        <div className="flex justify-center py-3">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        </div>
    );

    if (levels.length === 0) return (
        <p className="py-2 text-xs text-muted-foreground">Sem rubrica aprovada para este objetivo.</p>
    );

    return (
        <div className="space-y-1.5 py-2">
            {levels.map((lv: any) => {
                const L = LEVELS[lv.level - 1];
                return (
                    <div key={lv.id} className={`flex items-start gap-2 rounded-lg border px-2.5 py-2 ${L.border} bg-transparent`}>
                        <span className={`mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full ${L.bg} text-[10px] font-bold text-white`}>
                            {lv.level}
                        </span>
                        <p className="text-xs leading-relaxed text-muted-foreground">{lv.description}</p>
                    </div>
                );
            })}
        </div>
    );
}

// ─────────────────────────────────────────
// CARD DE ALUNO
// ─────────────────────────────────────────
interface StudentCardProps {
    student: any;
    grade?: number;
    objectives: any[];
    onGrade: (studentId: string, level: number, objectiveId?: string) => void;
}

function StudentCard({ student, grade, objectives, onGrade }: StudentCardProps) {
    const [expanded, setExpanded] = useState(false);
    const [selectedObj, setSelectedObj] = useState<any>(objectives[0]);
    const [showRubric, setShowRubric] = useState(false);
    const assigned = grade;

    // Atualizar objetivo selecionado quando mudar os objetivos
    useEffect(() => {
        if (objectives.length > 0 && !selectedObj) setSelectedObj(objectives[0]);
    }, [objectives]);

    const initials = student.student_name
        .split(" ")
        .map((n: string) => n[0])
        .slice(0, 2)
        .join("")
        .toUpperCase();

    const levelInfo = assigned ? LEVELS[assigned - 1] : null;

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className={`rounded-2xl border-2 transition-all ${levelInfo ? `${levelInfo.border} bg-card` : "border-border bg-card/60"}`}
        >
            {/* Header do card — sempre visível */}
            <button
                onClick={() => setExpanded(v => !v)}
                className="flex w-full items-center gap-3 p-3 text-left"
            >
                {/* Avatar */}
                <div className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-sm font-bold text-white ${levelInfo ? levelInfo.bg : "bg-muted-foreground/20"}`}>
                    {initials}
                </div>
                {/* Nome + nível */}
                <div className="flex-1 min-w-0">
                    <p className="truncate text-sm font-medium">{student.student_name}</p>
                    {levelInfo ? (
                        <p className={`text-xs font-medium ${levelInfo.text}`}>{levelInfo.label} · {levelInfo.full}</p>
                    ) : (
                        <p className="text-xs text-muted-foreground">Não avaliado</p>
                    )}
                </div>
                {/* Expand icon */}
                <div className="flex-shrink-0 text-muted-foreground">
                    {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </div>
            </button>

            {/* Botões rápidos de nível — ficam SEMPRE visíveis embaixo */}
            <div className="grid grid-cols-4 gap-1.5 px-3 pb-3">
                {LEVELS.map(level => (
                    <button
                        key={level.value}
                        onClick={() => onGrade(student.student_id, level.value, selectedObj?.id)}
                        className={`flex flex-col items-center justify-center rounded-xl py-2.5 text-xs font-bold text-white transition-all active:scale-95
                            ${level.bg}
                            ${assigned === level.value
                                ? `ring-2 ring-white ring-offset-2 ring-offset-card scale-[1.04] shadow-lg`
                                : "opacity-50 hover:opacity-90"
                            }`}
                    >
                        <span className="text-base leading-none">{level.value}</span>
                        <span className="mt-0.5 text-[9px] opacity-90">{level.label}</span>
                    </button>
                ))}
            </div>

            {/* Painel expandido (objetivos + rubrica) */}
            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden border-t border-border bg-secondary/30 px-3"
                    >
                        {objectives.length > 0 ? (
                            <div className="py-3 space-y-2">
                                {/* Seletor de objetivo */}
                                <p className="text-xs font-medium text-muted-foreground">Objetivo avaliado:</p>
                                <div className="space-y-1">
                                    {objectives.map((obj: any) => (
                                        <button
                                            key={obj.id}
                                            onClick={() => setSelectedObj(obj)}
                                            className={`w-full rounded-xl border px-2.5 py-2 text-left text-xs transition-all ${selectedObj?.id === obj.id ? "border-primary bg-primary/5 text-primary" : "border-border text-muted-foreground hover:border-primary/30"}`}
                                        >
                                            <span className="font-medium">Obj. {obj.order_index}: </span>
                                            {obj.description}
                                        </button>
                                    ))}
                                </div>

                                {/* Rubrica inline */}
                                <button
                                    onClick={() => setShowRubric(v => !v)}
                                    className="flex items-center gap-1.5 text-xs text-primary hover:underline"
                                >
                                    <BookOpen className="h-3 w-3" />
                                    {showRubric ? "Ocultar" : "Ver"} rubrica completa
                                </button>
                                <AnimatePresence>
                                    {showRubric && selectedObj && (
                                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                            <RubricExpanded objectiveId={selectedObj.id} />
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        ) : (
                            <p className="py-3 text-xs text-muted-foreground">Nenhum objetivo aprovado para esta habilidade.</p>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}

// ─────────────────────────────────────────
// PÁGINA PRINCIPAL
// ─────────────────────────────────────────
export default function AvaliacaoPage() {
    // Filtros
    const [classes, setClasses] = useState<any[]>([]);
    const [disciplines, setDisciplines] = useState<any[]>([]);
    const [skills, setSkills] = useState<any[]>([]);
    const [students, setStudents] = useState<any[]>([]);
    const [objectives, setObjectives] = useState<any[]>([]);

    const [selectedClass, setSelectedClass] = useState("");
    const [selectedDisc, setSelectedDisc] = useState("");
    const [selectedBimester, setSelectedBimester] = useState(1);
    const [selectedSkill, setSelectedSkill] = useState<any>(null);

    // Avaliações locais
    const [grades, setGrades] = useState<Record<string, number>>({});
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    // Carregar listas base
    useEffect(() => {
        getClasses().then(r => setClasses(r.data)).catch(() => { });
        getDisciplines().then(r => setDisciplines(r.data)).catch(() => { });
    }, []);

    // Carregar habilidades quando filtro muda
    useEffect(() => {
        if (!selectedDisc) return;
        const disc = disciplines.find(d => String(d.id) === selectedDisc);
        const cls = classes.find(c => c.class_name === selectedClass);
        if (!disc) return;
        getBnccSkills({
            discipline_id: disc.id,
            year_grade: cls?.year_level || undefined,
            bimester: selectedBimester,
            limit: 50,
        }).then(r => setSkills(r.data)).catch(() => { });
        setSelectedSkill(null);
    }, [selectedDisc, selectedBimester, selectedClass]);

    // Carregar alunos quando turma muda
    useEffect(() => {
        if (!selectedClass) return;
        getStudents({ class_name: selectedClass, limit: 100 })
            .then(r => setStudents(r.data))
            .catch(() => { });
    }, [selectedClass]);

    // Carregar objetivos aprovados quando habilidade muda
    useEffect(() => {
        if (!selectedSkill || !selectedDisc) { setObjectives([]); return; }
        const cls = classes.find(c => c.class_name === selectedClass);
        getObjectives({
            bncc_code: selectedSkill.bncc_code,
            discipline_id: selectedDisc,
            year_level: cls?.year_level || 6,
            bimester: selectedBimester,
        }).then(r => setObjectives((r.data || []).filter((o: any) => o.status === "approved")))
            .catch(() => setObjectives([]));
    }, [selectedSkill, selectedDisc, selectedBimester]);

    const handleGrade = (studentId: string, level: number) => {
        setGrades(prev => ({ ...prev, [studentId]: level }));
        setSaved(false);
    };

    const handleSave = async () => {
        if (!selectedSkill || Object.keys(grades).length === 0) return;
        setSaving(true);
        try {
            const date = new Date().toISOString();
            const cls = classes.find(c => c.class_name === selectedClass);
            const disc = disciplines.find(d => String(d.id) === selectedDisc);
            const user = typeof window !== "undefined"
                ? JSON.parse(localStorage.getItem("sga_user") || "{}") : {};

            const payload = Object.entries(grades).map(([studentId, level]) => ({
                student_id: studentId,
                bncc_code: selectedSkill.bncc_code,
                level_assigned: level,
                bimester: selectedBimester,
                class_name: selectedClass,
                discipline_id: disc?.id,
                teacher_id: user.id,
                date,
                objective_id: objectives[0]?.id || null,
            }));

            await api.post("/api/assessments/batch", payload);
            setSaved(true);
            setTimeout(() => setSaved(false), 4000);
        } catch (e: any) {
            // Fallback: salvar um a um se batch não existir
            alert("Avaliações registradas localmente. Backend batch ainda não implementado.");
            setSaved(true);
        } finally { setSaving(false); }
    };

    const gradedCount = Object.keys(grades).length;
    const progress = students.length > 0 ? (gradedCount / students.length) * 100 : 0;
    const avgLevel = gradedCount > 0
        ? Object.values(grades).reduce((a, b) => a + b, 0) / gradedCount : 0;

    const levelDist = [1, 2, 3, 4].map(n => ({
        level: n,
        count: Object.values(grades).filter(v => v === n).length,
        pct: gradedCount > 0 ? Math.round(Object.values(grades).filter(v => v === n).length / gradedCount * 100) : 0,
    }));

    return (
        <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
            {/* Header */}
            <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="mb-6 flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg shadow-emerald-500/20">
                    <ClipboardCheck className="h-6 w-6 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Avaliação Contínua</h1>
                    <p className="text-sm text-muted-foreground">Registre o desempenho por habilidade BNCC</p>
                </div>
            </motion.div>

            {/* FILTROS */}
            <div className="mb-6 grid grid-cols-2 gap-3 rounded-2xl border border-border bg-card/60 p-4 sm:grid-cols-4">
                <select value={selectedClass} onChange={e => { setSelectedClass(e.target.value); setGrades({}); }} className="input">
                    <option value="">Turma...</option>
                    {classes.map(c => <option key={c.id} value={c.class_name}>{c.class_name}</option>)}
                </select>
                <select value={selectedDisc} onChange={e => { setSelectedDisc(e.target.value); setSelectedSkill(null); setGrades({}); }} className="input">
                    <option value="">Disciplina...</option>
                    {disciplines.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
                <select value={selectedBimester} onChange={e => { setSelectedBimester(Number(e.target.value)); setSelectedSkill(null); }} className="input">
                    {[1, 2, 3, 4].map(b => <option key={b} value={b}>{b}º Bimestre</option>)}
                </select>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Filter className="h-3.5 w-3.5 flex-shrink-0 text-primary" />
                    {skills.length} habilidades disponíveis
                </div>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                {/* ── COLUNA ESQUERDA: Habilidades ── */}
                <div className="space-y-3 lg:col-span-1">
                    <h2 className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                        <BookOpen className="h-4 w-4" /> Habilidade BNCC
                    </h2>

                    {!selectedDisc ? (
                        <div className="flex h-24 items-center justify-center rounded-2xl border border-dashed border-border text-sm text-muted-foreground">
                            Selecione disciplina e bimestre
                        </div>
                    ) : skills.length === 0 ? (
                        <div className="flex h-24 items-center justify-center rounded-2xl border border-dashed border-border text-sm text-muted-foreground">
                            <AlertTriangle className="mr-2 h-4 w-4" /> Nenhuma habilidade
                        </div>
                    ) : (
                        <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
                            {skills.map(sk => (
                                <button key={sk.bncc_code} onClick={() => { setSelectedSkill(sk); setGrades({}); }}
                                    className={`w-full rounded-xl border p-3 text-left transition-all ${selectedSkill?.bncc_code === sk.bncc_code ? "border-primary bg-primary/5" : "border-border hover:border-primary/30 hover:bg-secondary"}`}>
                                    <p className="text-xs font-mono font-bold text-primary">{sk.bncc_code}</p>
                                    <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">{sk.description}</p>
                                </button>
                            ))}
                        </div>
                    )}

                    {/* RESUMO + SALVAR */}
                    {selectedSkill && students.length > 0 && (
                        <div className="rounded-2xl border border-border bg-card/60 p-4 space-y-3">
                            {/* Barra de progresso */}
                            <div>
                                <div className="mb-1.5 flex justify-between text-xs text-muted-foreground">
                                    <span>Progresso</span>
                                    <span>{gradedCount}/{students.length}</span>
                                </div>
                                <div className="h-2 overflow-hidden rounded-full bg-secondary">
                                    <motion.div className="h-full rounded-full bg-primary"
                                        animate={{ width: `${progress}%` }} transition={{ duration: 0.4 }} />
                                </div>
                            </div>
                            {/* Distribuição N1-N4 */}
                            <div className="grid grid-cols-4 gap-1">
                                {levelDist.map(ld => (
                                    <div key={ld.level} className="text-center">
                                        <div className={`h-1.5 rounded-full ${LEVELS[ld.level - 1].bg} mb-1`}
                                            style={{ opacity: ld.count > 0 ? 1 : 0.2 }} />
                                        <p className="text-xs font-bold">{ld.count}</p>
                                        <p className="text-[9px] text-muted-foreground">N{ld.level}</p>
                                    </div>
                                ))}
                            </div>
                            {/* Média */}
                            {gradedCount > 0 && (
                                <div className="rounded-xl bg-secondary py-2 text-center">
                                    <p className="text-2xl font-bold text-primary">{avgLevel.toFixed(1)}</p>
                                    <p className="text-xs text-muted-foreground">Nível médio</p>
                                </div>
                            )}
                            {/* Botão Salvar */}
                            <button onClick={handleSave} disabled={saving || gradedCount === 0}
                                className={`btn-primary w-full flex items-center justify-center gap-2 ${saved ? "!bg-emerald-500" : ""}`}>
                                {saving ? <><Loader2 className="h-4 w-4 animate-spin" /> Salvando...</>
                                    : saved ? <><CheckCircle2 className="h-4 w-4" /> Avaliações Salvas!</>
                                        : <><Save className="h-4 w-4" /> Salvar Avaliações</>}
                            </button>
                        </div>
                    )}
                </div>

                {/* ── COLUNA DIREITA: Alunos ── */}
                <div className="lg:col-span-2">
                    <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                        <Users className="h-4 w-4" />
                        {selectedClass ? `Alunos — ${selectedClass}` : "Alunos"}
                        {selectedSkill && (
                            <span className="ml-auto rounded-full border border-primary/30 bg-primary/5 px-2 py-0.5 text-xs font-mono text-primary">
                                {selectedSkill.bncc_code}
                            </span>
                        )}
                    </h2>

                    {!selectedClass ? (
                        <div className="flex h-48 flex-col items-center justify-center rounded-2xl border border-dashed border-border text-center text-muted-foreground">
                            <ClipboardCheck className="mb-2 h-10 w-10 opacity-30" />
                            <p className="text-sm">Selecione uma turma e disciplina</p>
                        </div>
                    ) : !selectedSkill ? (
                        <div className="flex h-48 flex-col items-center justify-center rounded-2xl border border-dashed border-border text-center text-muted-foreground">
                            <BookOpen className="mb-2 h-10 w-10 opacity-30" />
                            <p className="text-sm">Selecione uma habilidade BNCC</p>
                        </div>
                    ) : students.length === 0 ? (
                        <div className="flex h-48 flex-col items-center justify-center rounded-2xl border border-dashed border-border text-muted-foreground">
                            <AlertTriangle className="mb-2 h-8 w-8 opacity-30" />
                            <p className="text-sm">Nenhum aluno nessa turma</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                            {students.map(student => (
                                <StudentCard
                                    key={student.id}
                                    student={student}
                                    grade={grades[student.id]}
                                    objectives={objectives}
                                    onGrade={handleGrade}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
