"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Lightbulb, Sparkles, BookOpen, ChevronRight, Loader2,
    CheckCircle2, Save, Send, Info, RotateCcw, Plus, Minus
} from "lucide-react";
import { getBnccSkills, getDisciplines, getClassesYears, generateObjectives, submitObjective, generateRubrics } from "@/lib/api";

// ─────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────
type Step = 1 | 2 | 3 | 4;

interface Skill { bncc_code: string; description: string; year_grade: number; }
interface Objective { id?: string; description: string; explanation: string; order: number; }

// ─────────────────────────────────────────
// STEP INDICATOR
// ─────────────────────────────────────────
function StepIndicator({ current }: { current: Step }) {
    const steps = [
        { n: 1, label: "Disciplina" },
        { n: 2, label: "Habilidade" },
        { n: 3, label: "Bimestre" },
        { n: 4, label: "Objetivos" },
    ];
    return (
        <div className="flex items-center gap-1">
            {steps.map((s, i) => (
                <React.Fragment key={s.n}>
                    <div className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-all ${current >= s.n ? "bg-primary text-white" : "bg-secondary text-muted-foreground"}`}>
                        {current > s.n ? <CheckCircle2 className="h-4 w-4" /> : s.n}
                    </div>
                    <span className={`hidden text-xs font-medium sm:inline ${current === s.n ? "text-foreground" : "text-muted-foreground"}`}>{s.label}</span>
                    {i < steps.length - 1 && <div className={`mx-1 h-px w-6 flex-shrink-0 ${current > s.n ? "bg-primary" : "bg-border"}`} />}
                </React.Fragment>
            ))}
        </div>
    );
}

// ─────────────────────────────────────────
// OBJECTIVE CARD (editable)
// ─────────────────────────────────────────
function ObjectiveCard({
    obj, index, onEdit, saved
}: {
    obj: Objective; index: number; onEdit: (desc: string) => void; saved: boolean;
}) {
    const [expanded, setExpanded] = useState(false);
    const [editing, setEditing] = useState(false);
    const [draft, setDraft] = useState(obj.description);

    return (
        <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.08 }}
            className={`rounded-2xl border transition-all ${saved ? "border-emerald-500/30 bg-emerald-500/5" : "border-border bg-card/60"}`}>
            <div className="p-4">
                <div className="flex items-start gap-3">
                    {/* Number */}
                    <div className={`flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full text-xs font-bold ${saved ? "bg-emerald-500 text-white" : "bg-primary/10 text-primary"}`}>
                        {saved ? <CheckCircle2 className="h-4 w-4" /> : index + 1}
                    </div>
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                        {editing ? (
                            <div className="space-y-2">
                                <textarea value={draft} onChange={e => setDraft(e.target.value)} rows={3}
                                    className="input resize-none" />
                                <div className="flex gap-2">
                                    <button onClick={() => { onEdit(draft); setEditing(false); }}
                                        className="btn-primary flex items-center gap-1 py-1 px-3 text-xs">
                                        <Save className="h-3 w-3" /> Salvar edição
                                    </button>
                                    <button onClick={() => { setDraft(obj.description); setEditing(false); }}
                                        className="btn-secondary py-1 px-3 text-xs">Cancelar</button>
                                </div>
                            </div>
                        ) : (
                            <p className="text-sm leading-relaxed">{obj.description}</p>
                        )}

                        {obj.explanation && (
                            <button onClick={() => setExpanded(v => !v)}
                                className="mt-2 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
                                <Info className="h-3 w-3" />
                                {expanded ? "Ocultar" : "Ver"} fundamentação pedagógica
                                <ChevronRight className={`h-3 w-3 transition-transform ${expanded ? "rotate-90" : ""}`} />
                            </button>
                        )}
                        <AnimatePresence>
                            {expanded && obj.explanation && (
                                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}
                                    className="overflow-hidden">
                                    <p className="mt-2 rounded-xl bg-blue-500/5 border border-blue-500/15 p-3 text-xs text-muted-foreground leading-relaxed">
                                        {obj.explanation}
                                    </p>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                    {/* Edit button */}
                    {!saved && !editing && (
                        <button onClick={() => setEditing(true)}
                            className="flex-shrink-0 rounded-lg p-1.5 text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors">
                            ✏️
                        </button>
                    )}
                </div>
            </div>
        </motion.div>
    );
}

// ─────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────
export default function ConsultorPage() {
    const [step, setStep] = useState<Step>(1);

    // Seleções
    const [disciplines, setDisciplines] = useState<any[]>([]);
    const [availableYears, setAvailableYears] = useState<number[]>([]);
    const [selectedDisc, setSelectedDisc] = useState<any>(null);
    const [skills, setSkills] = useState<Skill[]>([]);
    const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
    const [selectedBimester, setSelectedBimester] = useState<number | null>(null);
    const [yearLevel, setYearLevel] = useState<number>(0);
    const [quantity, setQuantity] = useState<number>(3);

    // Resultados
    const [loading, setLoading] = useState(false);
    const [objectives, setObjectives] = useState<Objective[]>([]);
    const [draftIds, setDraftIds] = useState<string[]>([]);
    const [explanation, setExplanation] = useState("");
    const [saved, setSaved] = useState(false);
    const [saving, setSaving] = useState(false);

    // Carregar disciplinas e anos dinâmicos
    useEffect(() => {
        getDisciplines().then(r => setDisciplines(r.data)).catch(() => { });
        getClassesYears().then(r => {
            const yList = r.data || [];
            setAvailableYears(yList);
            if (yList.length > 0) setYearLevel(yList[0]);
        }).catch(() => { });
    }, []);

    // Auto-avanço Etapa 1 -> 2
    useEffect(() => {
        if (step === 1 && selectedDisc && yearLevel > 0) {
            setStep(2);
        }
    }, [selectedDisc, yearLevel, step]);

    // Auto-avanço Etapa 2 -> 3
    useEffect(() => {
        if (step === 2 && selectedSkill) {
            setStep(3);
        }
    }, [selectedSkill, step]);

    // Carregar habilidades
    useEffect(() => {
        if (!selectedDisc || !yearLevel) return;
        getBnccSkills({ discipline_id: selectedDisc.id, year_grade: yearLevel, limit: 100 })
            .then(r => setSkills(r.data))
            .catch(() => { });
    }, [selectedDisc, yearLevel]);

    const handleGenerate = async () => {
        if (!selectedDisc || !selectedSkill || !selectedBimester) return;
        setLoading(true);
        setSaved(false);
        const user = typeof window !== "undefined" ? JSON.parse(localStorage.getItem("sga_user") || "{}") : {};
        try {
            const r = await generateObjectives({
                bncc_code: selectedSkill.bncc_code,
                discipline_id: selectedDisc.id,
                year_level: yearLevel,
                bimester: selectedBimester,
                quantity,
                teacher_id: user.id || "00000000-0000-0000-0000-000000000000",
            });
            const objs: Objective[] = (r.data.objectives || []).map((d: string, i: number) => ({
                description: d,
                explanation: (r.data.explanations || [])[i] || r.data.explanation || "",
                order: i + 1,
                id: (r.data.draft_ids || [])[i],
            }));
            setObjectives(objs);
            setDraftIds(r.data.draft_ids || []);
            setExplanation(r.data.explanation || "");
            setStep(4);
        } catch (e: any) {
            alert(e?.response?.data?.detail || "Erro ao gerar objetivos.");
        } finally { setLoading(false); }
    };

    const handleSave = async () => {
        if (draftIds.length === 0) return;
        setSaving(true);
        const user = typeof window !== "undefined" ? JSON.parse(localStorage.getItem("sga_user") || "{}") : {};
        try {
            const results = await Promise.all(draftIds.map(id => submitObjective(id)));
            // Regra: se o objetivo constar como "approved" automaticamente, disparamos a geração de rubricas em background (fire-and-forget)
            results.forEach((res, index) => {
                if (res.data?.status === "approved") {
                    generateRubrics(draftIds[index], { teacher_id: user.id || "00000000-0000-0000-0000-000000000000" }).catch(() => { });
                }
            });
            setSaved(true);
        } catch (e: any) {
            alert(e?.response?.data?.detail || "Erro ao salvar.");
        } finally { setSaving(false); }
    };

    const handleReset = () => {
        setStep(1); setSelectedDisc(null); setSelectedSkill(null);
        setSelectedBimester(null); setObjectives([]); setDraftIds([]); setSaved(false);
    };

    return (
        <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6">
            {/* Header */}
            <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 shadow-lg shadow-violet-500/20">
                    <Lightbulb className="h-6 w-6 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Consultor Pedagógico</h1>
                    <p className="text-sm text-muted-foreground">Gere objetivos de aprendizagem progressivos com IA</p>
                </div>
            </motion.div>

            {/* Step Indicator */}
            <div className="rounded-2xl border border-border bg-card/60 p-4">
                <StepIndicator current={step} />
            </div>

            <AnimatePresence mode="wait">
                {/* STEP 1: DISCIPLINA */}
                {step === 1 && (
                    <motion.div key="s1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                        className="space-y-4">
                        <div className="rounded-2xl border border-border bg-card/60 p-5">
                            <p className="text-sm font-medium mb-4">1. Selecione a disciplina e o ano escolar</p>
                            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                                <div>
                                    <label className="text-xs text-muted-foreground mb-1 block">Disciplina</label>
                                    <select className="input" value={selectedDisc?.id || ""} onChange={e => {
                                        const d = disciplines.find(d => String(d.id) === e.target.value);
                                        setSelectedDisc(d || null);
                                    }}>
                                        <option value="">Selecione...</option>
                                        {disciplines.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs text-muted-foreground mb-1 block">Ano Escolar</label>
                                    <select className="input" value={yearLevel} onChange={e => setYearLevel(Number(e.target.value))}>
                                        {availableYears.length === 0 ? (
                                            <option value={0}>Nenhum ano escolar cadastrado</option>
                                        ) : (
                                            availableYears.map(y => <option key={y} value={y}>{y}º Ano</option>)
                                        )}
                                    </select>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* STEP 2: HABILIDADE */}
                {step === 2 && (
                    <motion.div key="s2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                        className="space-y-4">
                        <div className="rounded-2xl border border-border bg-card/60 p-5">
                            <div className="flex items-center justify-between mb-4">
                                <p className="text-sm font-medium">2. Selecione a habilidade BNCC</p>
                                <button onClick={() => setStep(1)} className="text-xs text-muted-foreground hover:text-foreground">Voltar</button>
                            </div>
                            {skills.length === 0 ? (
                                <p className="text-sm text-muted-foreground">Nenhuma habilidade encontrada para {selectedDisc?.name} · {yearLevel}º Ano.</p>
                            ) : (
                                <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                                    {skills.map(s => (
                                        <button key={s.bncc_code} onClick={() => setSelectedSkill(s)}
                                            className={`w-full rounded-xl border p-3 text-left transition-all ${selectedSkill?.bncc_code === s.bncc_code ? "border-primary bg-primary/5" : "border-border hover:border-primary/30 hover:bg-secondary"}`}>
                                            <div className="flex items-start gap-2">
                                                <span className="mt-0.5 rounded-lg bg-primary/10 px-2 py-0.5 text-xs font-mono text-primary">{s.bncc_code}</span>
                                                <p className="text-xs leading-relaxed">{s.description}</p>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}

                {/* STEP 3: BIMESTRE + CONFIGURAÇÃO */}
                {step === 3 && (
                    <motion.div key="s3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                        className="space-y-4">
                        <div className="rounded-2xl border border-border bg-card/60 p-5 space-y-5">
                            <p className="text-sm font-medium">3. Configure o bimestre e a quantidade de objetivos</p>

                            <div>
                                <label className="text-xs text-muted-foreground mb-2 block">Bimestre</label>
                                <div className="grid grid-cols-4 gap-2">
                                    {[1, 2, 3, 4].map(b => (
                                        <button key={b} onClick={() => setSelectedBimester(b)}
                                            className={`rounded-xl border py-3 text-sm font-medium transition-all ${selectedBimester === b ? "border-primary bg-primary text-white" : "border-border hover:border-primary/50"}`}>
                                            {b}º Bim
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <label className="text-xs text-muted-foreground mb-2 block">Quantidade de objetivos</label>
                                <div className="flex items-center gap-3">
                                    <button onClick={() => setQuantity(q => Math.max(1, q - 1))} className="btn-secondary p-2 rounded-lg"><Minus className="h-4 w-4" /></button>
                                    <span className="text-2xl font-bold w-8 text-center">{quantity}</span>
                                    <button onClick={() => setQuantity(q => Math.min(6, q + 1))} className="btn-secondary p-2 rounded-lg"><Plus className="h-4 w-4" /></button>
                                    <p className="text-xs text-muted-foreground">(1 a 6 objetivos)</p>
                                </div>
                            </div>

                            {/* Habilidade selecionada - preview */}
                            {selectedSkill && (
                                <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3">
                                    <p className="text-xs font-medium text-amber-400 mb-1">Habilidade selecionada</p>
                                    <p className="text-xs text-muted-foreground leading-relaxed">{selectedSkill.bncc_code}: {selectedSkill.description}</p>
                                </div>
                            )}

                            <div className="flex gap-2">
                                <button onClick={() => setStep(2)} className="btn-secondary">Voltar</button>
                                <button onClick={handleGenerate} disabled={!selectedBimester || loading}
                                    className="btn-primary flex flex-1 items-center justify-center gap-2">
                                    {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Gerando com IA...</>
                                        : <><Sparkles className="h-4 w-4" /> Gerar Objetivos</>}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* STEP 4: OBJETIVOS GERADOS */}
                {step === 4 && objectives.length > 0 && (
                    <motion.div key="s4" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
                        className="space-y-4">
                        {/* Explicação geral */}
                        {explanation && (
                            <div className="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-4">
                                <div className="flex items-center gap-2 mb-2">
                                    <Sparkles className="h-4 w-4 text-violet-400" />
                                    <p className="text-xs font-medium text-violet-400">Fundamentação Pedagógica Geral</p>
                                </div>
                                <p className="text-sm text-muted-foreground leading-relaxed">{explanation}</p>
                            </div>
                        )}

                        {/* Lista de objetivos */}
                        <div className="space-y-3">
                            {objectives.map((o, i) => (
                                <ObjectiveCard key={i} obj={o} index={i} saved={saved}
                                    onEdit={(desc) => setObjectives(prev => prev.map((p, j) => j === i ? { ...p, description: desc } : p))} />
                            ))}
                        </div>

                        {/* Ações */}
                        {!saved && (
                            <div className="flex gap-3">
                                <button onClick={handleGenerate} disabled={loading}
                                    className="btn-secondary flex items-center gap-2">
                                    <RotateCcw className="h-4 w-4" /> Regerar
                                </button>
                                <button onClick={handleSave} disabled={saving}
                                    className="btn-primary flex flex-1 items-center justify-center gap-2">
                                    {saving
                                        ? <><Loader2 className="h-4 w-4 animate-spin" /> Salvando...</>
                                        : <><Send className="h-4 w-4" /> Enviar para Aprovação</>}
                                </button>
                            </div>
                        )}

                        {saved && (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-4 text-center space-y-3">
                                <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-400" />
                                <p className="text-sm font-medium text-emerald-400">Objetivos enviados para aprovação!</p>
                                <p className="text-xs text-muted-foreground">Os professores da disciplina receberão uma notificação para revisar e aprovar.</p>
                                <button onClick={handleReset} className="btn-primary mx-auto flex items-center gap-2">
                                    <Plus className="h-4 w-4" /> Nova Geração
                                </button>
                            </motion.div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
