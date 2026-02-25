"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    FileCheck2, CheckCircle2, XCircle, Loader2, ChevronDown,
    ChevronUp, AlertTriangle, BookOpen, Clock, Info, Edit3, Save, X
} from "lucide-react";
import { getDisciplines, getClassesYears, getObjectives, approveObjective, getRubrics, generateRubrics, approveRubricLevel } from "@/lib/api";
import { diffWords } from "diff";

// ─────────────────────────────────────────
// Utils
// ─────────────────────────────────────────
function DiffText({ oldText, newText }: { oldText: string, newText: string }) {
    if (!oldText) return <p className="text-xs text-muted-foreground line-through opacity-70">{oldText}</p>;
    const diff = diffWords(oldText, newText);
    return (
        <p className="text-xs text-muted-foreground break-words whitespace-pre-wrap mt-2">
            {diff.map((part, index) => {
                if (part.added) return <span key={index} className="bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-semibold px-1 py-0.5 rounded">{part.value}</span>;
                if (part.removed) return <span key={index} className="bg-red-500/20 text-red-600 dark:text-red-400 line-through opacity-70 px-1 py-0.5 rounded mr-1">{part.value}</span>;
                return <span key={index}>{part.value}</span>;
            })}
        </p>
    );
}

// ─────────────────────────────────────────
// STATUS BADGE
// ─────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
    const conf: Record<string, { label: string; color: string; icon: React.ComponentType<any> }> = {
        draft: { label: "Rascunho", color: "bg-neutral-500/10 text-neutral-400 border-neutral-500/20", icon: Clock },
        pending: { label: "Pendente", color: "bg-amber-500/10  text-amber-400  border-amber-500/20", icon: Clock },
        approved: { label: "Aprovado", color: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20", icon: CheckCircle2 },
        rejected: { label: "Rejeitado", color: "bg-red-500/10    text-red-400    border-red-500/20", icon: XCircle },
    };
    const c = conf[status] || conf.pending;
    const Icon = c.icon;
    return (
        <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${c.color}`}>
            <Icon className="h-3 w-3" /> {c.label}
        </span>
    );
}

// ─────────────────────────────────────────
// RUBRIC LEVELS PANEL
// ─────────────────────────────────────────
function RubricsPanel({ objectiveId, teacherId, objectiveStatus, setObjectiveRubricStatus }: { objectiveId: string; teacherId: string; objectiveStatus: string; setObjectiveRubricStatus: (status: string) => void }) {
    const [rubrics, setRubrics] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);

    const load = () => {
        setLoading(true);
        getRubrics(objectiveId).then(r => {
            setRubrics(r.data);
            const statuses = r.data.map((ru: any) => ru.status);
            if (statuses.includes("pending")) setObjectiveRubricStatus("pending");
            else if (statuses.includes("rejected")) setObjectiveRubricStatus("rejected");
            else if (statuses.length > 0) setObjectiveRubricStatus("approved");
            else setObjectiveRubricStatus("none");
        }).catch(() => { }).finally(() => setLoading(false));
    };
    useEffect(() => { load(); }, [objectiveId]);

    const handleGenerate = async () => {
        setGenerating(true);
        try { await generateRubrics(objectiveId, { teacher_id: teacherId }); load(); }
        catch (e: any) { alert(e?.response?.data?.detail || "Erro ao gerar rubricas."); }
        finally { setGenerating(false); }
    };

    const handleApprove = async (rubricId: string, action: string, newDesc?: string) => {
        try { await approveRubricLevel(rubricId, { teacher_id: teacherId, action, new_description: newDesc }); load(); }
        catch (e: any) { alert(e?.response?.data?.detail || "Erro."); }
    };

    const levelColors = ["", "bg-red-500/10 border-red-500/20 text-red-400", "bg-amber-500/10 border-amber-500/20 text-amber-400", "bg-blue-500/10 border-blue-500/20 text-blue-400", "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"];
    const levelLabels = ["", "N1 — Iniciante", "N2 — Em Desenvolvimento", "N3 — Proficiente", "N4 — Avançado"];

    if (loading) return <div className="flex justify-center py-4"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>;

    if (rubrics.length === 0) {
        return (
            <div className="space-y-3 p-3">
                <p className="text-xs text-muted-foreground">Nenhuma rubrica cadastrada para este objetivo.</p>
                {objectiveStatus === "approved" ? (
                    <button onClick={handleGenerate} disabled={generating}
                        className="btn-primary flex items-center gap-2 text-xs py-2 px-3">
                        {generating ? <Loader2 className="h-3 w-3 animate-spin" /> : "✨"}
                        {generating ? "Gerando..." : "Gerar rubricas com IA"}
                    </button>
                ) : (
                    <div className="rounded-lg bg-amber-500/10 p-3 text-xs text-amber-500 border border-amber-500/20 flex gap-2">
                        <AlertTriangle className="h-4 w-4 shrink-0" />
                        <p>A geração das rubricas só estará liberada após este Objetivo ser <strong>Aprovado</strong>.</p>
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="space-y-2 p-3">
            {rubrics.map((r: any) => (
                <RubricItem key={r.id} r={r} teacherId={teacherId} levelColors={levelColors} levelLabels={levelLabels} handleApprove={handleApprove} />
            ))}
        </div>
    );
}

function RubricItem({ r, teacherId, levelColors, levelLabels, handleApprove }: any) {
    const [isEditing, setIsEditing] = useState(false);
    const [editDesc, setEditDesc] = useState(r.description);
    const [acting, setActing] = useState(false);

    const onSave = async () => {
        if (editDesc === r.description) { setIsEditing(false); return; }
        setActing(true);
        await handleApprove(r.id, "edited", editDesc);
        setIsEditing(false);
        setActing(false);
    };

    const lastEditIndex = r.approvals ? r.approvals.map((a: any) => a.action).lastIndexOf("edited") : -1;
    const lastEdit = lastEditIndex !== -1 ? r.approvals[lastEditIndex] : null;
    const recentApprovals = r.approvals ? r.approvals.slice(lastEditIndex !== -1 ? lastEditIndex + 1 : 0) : [];
    const canAct = r.status === "pending" && !recentApprovals.some((a: any) => a.teacher_id === teacherId && a.action === "approved");

    return (
        <div className={`rounded-xl border p-3 ${levelColors[r.level] || ""}`}>
            <div className="flex items-start justify-between gap-2">
                <div className="space-y-1 flex-1">
                    <p className="text-xs font-semibold">{levelLabels[r.level]}</p>

                    {isEditing ? (
                        <div className="mt-2 space-y-2">
                            <textarea className="input text-xs min-h-[80px]" value={editDesc} onChange={e => setEditDesc(e.target.value)} />
                            <div className="flex gap-2">
                                <button onClick={onSave} disabled={acting} className="bg-primary hover:bg-primary/90 text-primary-foreground text-xs py-1.5 px-3 rounded-lg flex gap-1 items-center transition-colors">
                                    {acting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />} Enviar para Aprovação
                                </button>
                                <button onClick={() => { setIsEditing(false); setEditDesc(r.description); }} className="bg-secondary hover:bg-secondary/80 text-foreground text-xs py-1.5 px-3 rounded-lg transition-colors">Cancelar</button>
                            </div>
                        </div>
                    ) : (
                        <>
                            {lastEdit && (
                                <div className="mb-2 rounded-lg bg-background/50 p-2 border border-border">
                                    <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider flex items-center gap-1">
                                        <Info className="w-3 h-3" /> Modificações Requeridas (por {lastEdit.teacher_name}):
                                    </p>
                                    <DiffText oldText={lastEdit.previous_description} newText={r.description} />
                                </div>
                            )}
                            <p className="text-xs leading-relaxed text-foreground/90 whitespace-pre-wrap">{r.description}</p>
                        </>
                    )}
                </div>
                <div className="flex flex-col items-end gap-2">
                    <StatusBadge status={r.status} />
                    {!isEditing && (
                        <div className="flex gap-1.5 mt-1">
                            {canAct && (
                                <button onClick={() => { setActing(true); handleApprove(r.id, "approved").finally(() => setActing(false)); }} disabled={acting}
                                    className="rounded-lg bg-emerald-500 p-1.5 text-white hover:bg-emerald-600 transition-colors shadow-sm" title="Aprovar">
                                    {acting ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle2 className="h-3 w-3" />}
                                </button>
                            )}
                            <button onClick={() => setIsEditing(true)}
                                className="rounded-lg bg-secondary p-1.5 text-foreground hover:bg-secondary/80 transition-colors border border-border shadow-sm" title="Editar">
                                <Edit3 className="h-3 w-3" />
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────
// OBJECTIVE CARD
// ─────────────────────────────────────────
function ObjectiveItem({ obj, teacherId, onRefresh }: { obj: any; teacherId: string; onRefresh: () => void }) {
    const [expanded, setExpanded] = useState(false);
    const [acting, setActing] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [editDesc, setEditDesc] = useState(obj.description);
    const [rubricStatus, setRubricStatus] = useState<string>("none");

    const handleAction = async (action: string, newDesc?: string) => {
        setActing(true);
        try {
            const res = await approveObjective(obj.id, { teacher_id: teacherId, action, new_description: newDesc, notes: newDesc ? "Edição efetuada" : undefined });
            if (res.data?.status === "approved" && obj.status !== "approved" && !obj.has_rubrics) {
                generateRubrics(obj.id, { teacher_id: teacherId }).catch(() => { });
            }
            onRefresh();
        }
        catch (e: any) { alert(e?.response?.data?.detail || "Erro."); }
        finally { setActing(false); }
    };

    const onSave = async () => {
        if (editDesc === obj.description) { setIsEditing(false); return; }
        await handleAction("edited", editDesc);
        setIsEditing(false);
    };

    const lastEditIndex = obj.approvals ? obj.approvals.map((a: any) => a.action).lastIndexOf("edited") : -1;
    const lastEdit = lastEditIndex !== -1 ? obj.approvals[lastEditIndex] : null;
    const recentApprovals = obj.approvals ? obj.approvals.slice(lastEditIndex !== -1 ? lastEditIndex + 1 : 0) : [];
    const canAct = obj.status === "pending" && !recentApprovals.some((a: any) => a.teacher_id === teacherId && a.action === "approved");

    // Lógica para status composto
    let compoundMsg = "";
    if (obj.status === "approved") {
        if (rubricStatus === "pending") compoundMsg = "Objetivo Aprovado, aguardando Rubricas.";
        else if (rubricStatus === "approved") compoundMsg = "Objetivo e Rubricas Aprovados. ✅";
    }

    return (
        <div className={`rounded-2xl border transition-all overflow-hidden ${obj.status === "approved" ? "bg-card border-emerald-500/30" : "bg-card/60 border-border"}`}>
            <div className="p-4">
                <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-xs font-mono text-muted-foreground bg-secondary px-2 py-0.5 rounded-md">Obj. {obj.order_index}</span>
                            <StatusBadge status={obj.status} />
                            {compoundMsg && <span className="text-xs font-medium text-emerald-500">{compoundMsg}</span>}
                        </div>
                        {isEditing ? (
                            <div className="space-y-3 mt-3">
                                <textarea className="input text-sm min-h-[100px]" value={editDesc} onChange={e => setEditDesc(e.target.value)} />
                                <div className="flex gap-2">
                                    <button onClick={onSave} disabled={acting} className="bg-primary hover:bg-primary/90 text-primary-foreground text-xs py-1.5 px-4 rounded-lg flex gap-1 items-center transition-colors">
                                        {acting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Enviar para Aprovação
                                    </button>
                                    <button onClick={() => { setIsEditing(false); setEditDesc(obj.description); }} className="bg-secondary hover:bg-secondary/80 text-foreground text-xs py-1.5 px-4 rounded-lg transition-colors border border-border">Cancelar</button>
                                </div>
                            </div>
                        ) : (
                            <>
                                {lastEdit && (
                                    <div className="mb-3 rounded-xl bg-secondary/50 p-3 border border-border">
                                        <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-wider flex items-center gap-1.5">
                                            <Info className="w-3.5 h-3.5" /> Modificações (por {lastEdit.teacher_name}):
                                        </p>
                                        <DiffText oldText={lastEdit.previous_description} newText={obj.description} />
                                    </div>
                                )}
                                <p className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">{obj.description}</p>
                            </>
                        )}
                    </div>
                    <div className="flex flex-col items-end gap-2 shrink-0">
                        <button onClick={() => setExpanded(v => !v)}
                            className="flex-shrink-0 rounded-lg p-1.5 text-muted-foreground hover:bg-secondary transition-colors border border-transparent hover:border-border">
                            {expanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                        </button>
                    </div>
                </div>

                {/* Actions */}
                {!isEditing && (
                    <div className="mt-4 flex items-center justify-between">
                        <div className="flex gap-2">
                            {canAct && (
                                <button onClick={() => handleAction("approved")} disabled={acting}
                                    className="flex items-center gap-1.5 rounded-xl bg-emerald-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-600 disabled:opacity-50 shadow-sm transition-colors">
                                    {acting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                                    Aprovar
                                </button>
                            )}
                            <button onClick={() => setIsEditing(true)}
                                className="flex items-center gap-1.5 rounded-xl bg-secondary border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-secondary/80 transition-colors shadow-sm">
                                <Edit3 className="h-3.5 w-3.5" /> Editar
                            </button>
                        </div>
                        {/* Approvals history */}
                        {obj.approvals?.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 justify-end max-w-[50%]">
                                {obj.approvals.filter((a: any) => a.action === "approved").map((a: any, i: number) => (
                                    <span key={i} className="text-[10px] rounded-md px-2 py-0.5 bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 font-medium">
                                        ✓ {a.teacher_name}
                                    </span>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Rubrics panel */}
            <AnimatePresence>
                {expanded && (
                    <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }}
                        className="overflow-hidden border-t border-border bg-secondary/30">
                        <div className="p-1">
                            <p className="px-3 py-2 text-xs font-medium text-muted-foreground">📊 Rubricas de Avaliação (4 Níveis)</p>
                            <RubricsPanel objectiveId={obj.id} teacherId={teacherId} objectiveStatus={obj.status} setObjectiveRubricStatus={setRubricStatus} />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

// ─────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────
export default function ObjetivosPage() {
    const [disciplines, setDisciplines] = useState<any[]>([]);
    const [availableYears, setAvailableYears] = useState<number[]>([]);
    const [selectedDisc, setSelectedDisc] = useState<string>("");
    const [yearLevel, setYearLevel] = useState<number>(0);
    const [bimester, setBimester] = useState<number>(1);
    const [objectives, setObjectives] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");

    // Novo Estado de viewMode suportará "all", "approved", "pending", "draft"
    const [viewMode, setViewMode] = useState<"all" | "approved" | "pending" | "draft">("all");

    const teacherId = typeof window !== "undefined"
        ? JSON.parse(localStorage.getItem("sga_user") || "{}").id || ""
        : "";

    useEffect(() => {
        getDisciplines().then(r => setDisciplines(r.data)).catch(() => { });
        getClassesYears().then(r => {
            const yList = r.data || [];
            setAvailableYears(yList);
            if (yList.length > 0) {
                setYearLevel(yList[0]);
            }
        }).catch(() => { });
    }, []);

    const load = async () => {
        if (!selectedDisc) return;
        setLoading(true);
        try {
            const r = await getObjectives({
                bncc_code: "_all",
                discipline_id: selectedDisc,
                year_level: yearLevel,
                bimester,
            });
            setObjectives(r.data);
        } catch { } finally { setLoading(false); }
    };

    useEffect(() => { if (selectedDisc) load(); }, [selectedDisc, yearLevel, bimester]);

    const filtered = objectives.filter(o => {
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        return o.description.toLowerCase().includes(q) || (o.bncc_code && o.bncc_code.toLowerCase().includes(q));
    });

    // 1. Agrupar logicamente por Habilidade (código BNCC) para ditar o "Status da Habilidade"
    const groupedSkills = filtered.reduce((acc, curr) => {
        const code = curr.bncc_code || "Sem BNCC vinculada";
        if (!acc[code]) acc[code] = { description: curr.bncc_description || "", items: [] };
        acc[code].items.push(curr);
        return acc;
    }, {} as Record<string, { description: string, skillStatus: string, items: any[] }>);

    // 2. Calcular o Compound Status da Habilidade
    const groupsArray = Object.entries(groupedSkills).map(([code, data]: [string, any]) => {
        let allStatuses: string[] = [];
        data.items.forEach((o: any) => {
            allStatuses.push(o.status);
            if (o.has_rubrics && o.rubrics_status) {
                allStatuses.push(o.rubrics_status);
            } else if (o.status === "approved" && !o.has_rubrics) {
                // Objetivo aprovado sem rubricas cadastradas = Planejamento Pendente
                allStatuses.push("pending");
            }
        });

        let skillStatus = "draft";
        if (allStatuses.includes("rejected")) skillStatus = "rejected";
        else if (allStatuses.includes("pending")) skillStatus = "pending";
        else if (allStatuses.every(s => s === "approved")) skillStatus = "approved";

        return { code, description: data.description, skillStatus, items: data.items };
    });

    const stats = {
        total: groupsArray.length,
        approved: groupsArray.filter(g => g.skillStatus === "approved").length,
        pending: groupsArray.filter(g => g.skillStatus === "pending").length,
        draft: groupsArray.filter(g => g.skillStatus === "draft").length,
    };

    return (
        <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-6">
            {/* Header */}
            <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-lg shadow-emerald-500/20">
                    <FileCheck2 className="h-6 w-6 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Objetivos e Rubricas</h1>
                    <p className="text-sm text-muted-foreground">Revise e aprove os objetivos de aprendizagem e rubricas</p>
                </div>
            </motion.div>

            {/* Filtros */}
            <div className="grid grid-cols-1 gap-3 rounded-2xl border border-border bg-card/60 p-4 sm:grid-cols-4">
                <select className="input" value={selectedDisc} onChange={e => setSelectedDisc(e.target.value)}>
                    <option value="">Disciplina...</option>
                    {disciplines.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
                <select className="input" value={yearLevel} onChange={e => setYearLevel(Number(e.target.value))}>
                    {availableYears.length === 0 ? (
                        <option value={0}>Nenhum ano escolar cadastrado</option>
                    ) : (
                        availableYears.map(y => <option key={y} value={y}>{y}º Ano</option>)
                    )}
                </select>
                <select className="input" value={bimester} onChange={e => setBimester(Number(e.target.value))}>
                    {[1, 2, 3, 4].map(b => <option key={b} value={b}>{b}º Bimestre</option>)}
                </select>
                <input className="input" placeholder="Buscar habilidade ou objetivo..." value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)} />
            </div>

            {/* Cards Interativos */}
            {groupsArray.length > 0 && (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    {[
                        { id: "all", label: "Total", value: stats.total, color: "text-foreground", activeBg: "bg-secondary border-primary/30" },
                        { id: "approved", label: "Aprovadas", value: stats.approved, color: "text-emerald-500", activeBg: "bg-emerald-500/10 border-emerald-500/30" },
                        { id: "pending", label: "Pendentes", value: stats.pending, color: "text-amber-500", activeBg: "bg-amber-500/10 border-amber-500/30" },
                        { id: "draft", label: "Rascunhos", value: stats.draft, color: "text-neutral-500", activeBg: "bg-neutral-500/10 border-neutral-500/30" },
                    ].map(s => (
                        <button key={s.id} onClick={() => setViewMode(s.id as any)}
                            className={`rounded-xl border transition-all text-center p-3 hover:-translate-y-1 ${viewMode === s.id ? s.activeBg + ' shadow-md scale-[1.02]' : 'border-border bg-card/60 hover:bg-secondary/50'}`}>
                            <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
                            <p className="text-xs text-muted-foreground font-medium">{s.label}</p>
                        </button>
                    ))}
                </div>
            )}

            {/* List */}
            {(() => {
                const displayGroups = viewMode === "all" ? groupsArray : groupsArray.filter(g => g.skillStatus === viewMode);

                if (!selectedDisc) return (
                    <div className="flex flex-col items-center justify-center py-20 text-center text-muted-foreground">
                        <BookOpen className="mb-3 h-10 w-10 opacity-30" />
                        <p className="text-sm">Selecione uma disciplina para ver os objetivos</p>
                    </div>
                );

                if (loading) return (
                    <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
                );

                if (displayGroups.length === 0) return (
                    <div className="flex flex-col items-center justify-center py-20 text-center text-muted-foreground bg-card/60 rounded-2xl border border-border">
                        <AlertTriangle className="mb-3 h-10 w-10 opacity-30" />
                        <p className="text-sm">Nenhum grupo de habilidade encontrado para esta visualização.</p>
                        <p className="text-xs mt-1">Acione o filtro ou use o Consultor Pedagógico.</p>
                    </div>
                );

                return (
                    <div className="space-y-8">
                        {displayGroups.map((group) => {
                            return (
                                <div key={group.code} className="space-y-4">
                                    <div className="px-1 border-b pb-2">
                                        <h3 className="text-lg font-bold flex items-center gap-3">
                                            <span className="bg-emerald-500/15 text-emerald-500 px-2.5 py-1 rounded-lg text-sm font-mono border border-emerald-500/20">{group.code}</span>
                                            <StatusBadge status={group.skillStatus} />
                                        </h3>
                                        {group.description && <p className="text-sm text-muted-foreground mt-2 leading-relaxed max-w-3xl">{group.description}</p>}
                                    </div>
                                    <div className="grid gap-3 border-l-2 border-emerald-500/30 pl-4 py-1">
                                        {group.items.map((o: any) => (
                                            <ObjectiveItem key={o.id} obj={o} teacherId={teacherId} onRefresh={load} />
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                );
            })()}
        </div>
    );
}
