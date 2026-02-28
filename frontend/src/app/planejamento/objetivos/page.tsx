"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    FileCheck2, CheckCircle2, XCircle, Loader2, ChevronDown,
    ChevronUp, AlertTriangle, BookOpen, Clock, Info, Edit3, Save, X
} from "lucide-react";
import { getDisciplines, getClassesYears, getObjectives, approveObjective, getRubrics, generateRubrics, approveRubricLevel, getTeacherClass } from "@/lib/api";
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
// HISTORY MODAL
// ─────────────────────────────────────────
function HistoryModal({ isOpen, onClose, approvals, title, currentDescription }: { isOpen: boolean; onClose: () => void; approvals: any[]; title: string; currentDescription: string }) {
    if (!isOpen) return null;
    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
            <div className="bg-card border border-border rounded-2xl shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="p-4 border-b border-border flex justify-between items-center bg-secondary/30">
                    <h2 className="text-lg font-bold flex items-center gap-2"><Clock className="w-5 h-5 text-primary" /> Histórico de Modificações - {title}</h2>
                    <button onClick={onClose} className="p-2 hover:bg-secondary rounded-full border border-transparent hover:border-border transition-colors"><X className="w-5 h-5 text-muted-foreground" /></button>
                </div>
                <div className="p-6 overflow-y-auto flex-1 space-y-0">
                    {approvals.length === 0 ? <p className="text-muted-foreground">Nenhuma modificação registrada.</p> : approvals.map((a: any, i: number) => (
                        <div key={i} className="flex gap-4">
                            <div className="flex flex-col items-center">
                                <div className="w-4 h-4 rounded-full bg-primary/20 border-2 border-primary mt-1 shadow-sm shrink-0"></div>
                                {i < approvals.length - 1 && <div className="w-0.5 h-full bg-border my-1"></div>}
                            </div>
                            <div className="flex-1 pb-6">
                                <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-2">
                                    <span className="font-mono bg-secondary px-2 py-0.5 rounded text-xs font-semibold whitespace-nowrap border border-border shadow-sm">{new Date(a.created_at).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                                    <strong className="text-foreground text-sm">{a.teacher_name}</strong>
                                    <span className={`text-xs font-bold border px-1.5 py-0.5 rounded-md ${a.action === 'approved' ? 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20' : a.action === 'rejected' ? 'text-red-500 bg-red-500/10 border-red-500/20' : 'text-blue-500 bg-blue-500/10 border-blue-500/20'}`}>
                                        {a.action === 'approved' ? 'Aprovou' : a.action === 'rejected' ? 'Rejeitou' : a.action === 'edited' ? 'Editou' : a.action === 'reopen' ? 'Reabriu' : a.action}
                                    </span>
                                </div>
                                {a.notes && <p className="italic text-muted-foreground text-sm mb-3">"{a.notes}"</p>}
                                {a.action === 'edited' && a.previous_description && (
                                    <div className="p-4 bg-secondary/30 rounded-xl border border-border mt-2 shadow-sm">
                                        <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5"><Info className="w-3.5 h-3.5" /> Alterações detectadas:</p>
                                        <div className="text-sm">
                                            <DiffText oldText={a.previous_description} newText={currentDescription} />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
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
function RubricsPanel({ objectiveId, teacherId, userRole, objectiveStatus, setObjectiveRubricStatus }: { objectiveId: string; teacherId: string; userRole: string; objectiveStatus: string; setObjectiveRubricStatus: (status: string) => void }) {
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4">
            {rubrics.map((r: any) => (
                <RubricItem key={r.id} r={r} teacherId={teacherId} userRole={userRole} levelColors={levelColors} levelLabels={levelLabels} handleApprove={handleApprove} />
            ))}
        </div>
    );
}

function RubricItem({ r, teacherId, userRole, levelColors, levelLabels, handleApprove }: any) {
    const [isEditing, setIsEditing] = useState(false);
    const [editDesc, setEditDesc] = useState(r.description);
    const [acting, setActing] = useState(false);
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);

    const onSave = async () => {
        if (editDesc === r.description) {
            // Se for apenas rascunho sem mudar, nós fechamos aprovando para dar agilidade
            if (r.status === "draft" || r.status === "pending") {
                setActing(true);
                await handleApprove(r.id, "approved");
                setIsEditing(false);
                setActing(false);
            } else {
                setIsEditing(false);
            }
            return;
        }
        setActing(true);
        await handleApprove(r.id, "edited", editDesc);
        setIsEditing(false);
        setActing(false);
    };

    const lastEditIndex = r.approvals ? r.approvals.map((a: any) => a.action).lastIndexOf("edited") : -1;
    const lastEdit = lastEditIndex !== -1 ? r.approvals[lastEditIndex] : null;
    const recentApprovals = r.approvals ? r.approvals.slice(lastEditIndex !== -1 ? lastEditIndex + 1 : 0) : [];
    // Só pode editar ou aprovar se NÃO estiver approved geral.
    const canAct = (r.status === "pending" || r.status === "draft") && !recentApprovals.some((a: any) => a.teacher_id === teacherId && a.action === "approved");
    const canEdit = r.status !== "approved";
    const canReopen = r.status === "approved" && (userRole === "admin" || userRole === "coordinator");

    return (
        <div className={`rounded-xl border p-3.5 ${levelColors[r.level] || ""}`}>
            <div className="flex flex-col gap-3">

                {/* Cabeçalho: Título e Status */}
                <div className="flex items-center justify-between gap-2 border-b border-border/30 pb-2">
                    <p className="text-xs font-bold uppercase tracking-wider">{levelLabels[r.level]}</p>
                    <StatusBadge status={r.status} />
                </div>

                {/* Corpo: Texto ou Área de Edição - Agora 100% da largura */}
                <div className="w-full">
                    {isEditing ? (
                        <div className="mt-1 space-y-2">
                            <textarea className="input text-xs min-h-[90px] w-full" value={editDesc} onChange={e => setEditDesc(e.target.value)} />
                            <div className="flex gap-2">
                                <button onClick={onSave} disabled={acting} className="bg-primary hover:bg-primary/90 text-primary-foreground text-xs py-1.5 px-3 rounded-lg flex gap-1 items-center transition-colors">
                                    {acting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />} Enviar
                                </button>
                                <button onClick={() => { setIsEditing(false); setEditDesc(r.description); }} className="bg-secondary hover:bg-secondary/80 text-foreground text-xs py-1.5 px-3 rounded-lg transition-colors">Cancelar</button>
                            </div>
                        </div>
                    ) : (
                        <>
                            <p className="text-xs leading-relaxed text-foreground/90 whitespace-pre-wrap">{r.description}</p>
                            {r.approvals && r.approvals.length > 0 && (
                                <div className="mt-3">
                                    <button onClick={() => setIsHistoryOpen(true)} className="text-[10px] font-medium text-primary hover:underline flex items-center gap-1 w-fit">
                                        <Clock className="w-3 h-3" /> Ver Histórico de Modificações ({r.approvals.length})
                                    </button>
                                    <HistoryModal isOpen={isHistoryOpen} onClose={() => setIsHistoryOpen(false)} approvals={r.approvals} title={`Rubrica ${levelLabels[r.level]}`} currentDescription={r.description} />
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* Rodapé: Carimbos e Ações */}
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2 border-t border-border/30">

                    {/* Lista de Aprovações */}
                    <div className="flex-1">
                        {r.required_teachers?.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                                {r.required_teachers.map((rt: any) => {
                                    const hasApproved = recentApprovals.some((a: any) => a.teacher_id === rt.id && a.action === "approved");
                                    return (
                                        <span key={rt.id} className={`text-[9px] rounded-md border px-1.5 py-0.5 font-medium flex items-center gap-1 ${hasApproved ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30" : "bg-red-500/5 text-red-500/60 dark:text-red-400/60 border-red-500/20"}`}>
                                            {hasApproved ? <CheckCircle2 className="w-2.5 h-2.5" /> : <Clock className="w-2.5 h-2.5" />} {rt.name.split(" ")[0]}
                                        </span>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    {!isEditing && (
                        <div className="flex items-center gap-1.5 justify-end shrink-0">
                            {canAct && (
                                <button onClick={() => { setActing(true); handleApprove(r.id, "approved").finally(() => setActing(false)); }} disabled={acting}
                                    className="rounded-lg bg-emerald-500 py-1.5 px-3 text-white focus:ring-2 focus:ring-emerald-500/50 hover:bg-emerald-600 transition-colors shadow-sm text-xs font-medium flex gap-1 items-center" title="Aprovar">
                                    {acting ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle2 className="h-3 w-3" />} Aprovar
                                </button>
                            )}
                            {canEdit && (
                                <button onClick={() => setIsEditing(true)}
                                    className="rounded-lg bg-secondary py-1.5 px-3 text-foreground hover:bg-secondary/80 transition-colors border border-border shadow-sm text-xs font-medium focus:ring-2 focus:ring-primary/20 flex gap-1 items-center" title="Editar">
                                    <Edit3 className="h-3 w-3" /> Editar
                                </button>
                            )}
                            {canReopen && (
                                <button onClick={() => { setActing(true); handleApprove(r.id, "reopen").finally(() => setActing(false)); }} disabled={acting}
                                    className="rounded-lg bg-amber-500/10 border border-amber-500/30 py-1.5 px-2 text-amber-500 hover:bg-amber-500/20 transition-colors shadow-sm focus:ring-2 focus:ring-amber-500/20" title="Reabrir Edição">
                                    {acting ? <Loader2 className="h-3 w-3 animate-spin" /> : <X className="h-3 w-3" />}
                                </button>
                            )}
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
function ObjectiveItem({ obj, teacherId, userRole, onRefresh }: { obj: any; teacherId: string; userRole: string; onRefresh: () => void }) {
    const [expanded, setExpanded] = useState(false);
    const [acting, setActing] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [editDesc, setEditDesc] = useState(obj.description);
    const [rubricStatus, setRubricStatus] = useState<string>("none");
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);

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
        if (editDesc === obj.description) {
            if (obj.status === "draft" || obj.status === "pending") {
                await handleAction("approved");
            }
            setIsEditing(false);
            return;
        }
        await handleAction("edited", editDesc);
        setIsEditing(false);
    };

    const lastEditIndex = obj.approvals ? obj.approvals.map((a: any) => a.action).lastIndexOf("edited") : -1;
    const lastEdit = lastEditIndex !== -1 ? obj.approvals[lastEditIndex] : null;
    const recentApprovals = obj.approvals ? obj.approvals.slice(lastEditIndex !== -1 ? lastEditIndex + 1 : 0) : [];

    const canAct = (obj.status === "pending" || obj.status === "draft") && !recentApprovals.some((a: any) => a.teacher_id === teacherId && a.action === "approved");
    const canEdit = obj.status !== "approved";
    const canReopen = obj.status === "approved" && (userRole === "admin" || userRole === "coordinator");

    // Lógica para status composto
    let compoundMsg = "";
    if (obj.status === "approved") {
        if (!obj.has_rubrics || obj.rubrics_status === "pending") {
            compoundMsg = "Objetivo Aprovado, aguardando Rubricas.";
        } else if (obj.rubrics_status === "approved") {
            compoundMsg = "Objetivo e Rubricas Aprovados. ✅";
        }
    }

    const handleApproveAllRubrics = async () => {
        setActing(true);
        try {
            const r = await getRubrics(obj.id);
            const rubricas = r.data || [];
            const pends = rubricas.filter((ru: any) => ru.status === "pending" || ru.status === "draft");
            const promessas = pends.map((ru: any) => approveRubricLevel(ru.id, { teacher_id: teacherId, action: "approved" }));
            await Promise.all(promessas);
            onRefresh();
        } catch (e: any) { alert("Erro ao aprovar rubricas em lote."); }
        finally { setActing(false); }
    };

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
                                <p className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">{obj.description}</p>
                                {obj.approvals && obj.approvals.length > 0 && (
                                    <div className="mt-4">
                                        <button onClick={() => setIsHistoryOpen(true)} className="text-xs font-medium text-primary hover:underline flex items-center gap-1 w-fit">
                                            <Clock className="w-3.5 h-3.5" /> Ver Histórico de Modificações ({obj.approvals.length})
                                        </button>
                                        <HistoryModal isOpen={isHistoryOpen} onClose={() => setIsHistoryOpen(false)} approvals={obj.approvals} title={`Objetivo ${obj.order_index}`} currentDescription={obj.description} />
                                    </div>
                                )}
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
                            {canEdit && (
                                <button onClick={() => setIsEditing(true)}
                                    className="flex items-center gap-1.5 rounded-xl bg-secondary border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-secondary/80 transition-colors shadow-sm">
                                    <Edit3 className="h-3.5 w-3.5" /> Editar
                                </button>
                            )}
                            {canReopen && (
                                <button onClick={() => handleAction("reopen")} disabled={acting}
                                    className="flex items-center gap-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 px-3 py-1.5 text-xs font-medium text-amber-500 hover:bg-amber-500/20 disabled:opacity-50 shadow-sm transition-colors">
                                    {acting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <X className="h-3.5 w-3.5" />}
                                    Reabrir Edição
                                </button>
                            )}
                            {obj.status === "approved" && obj.has_rubrics && obj.rubrics_status !== "approved" && (
                                <button onClick={handleApproveAllRubrics} disabled={acting}
                                    className="flex items-center gap-1.5 rounded-xl bg-blue-500/10 border border-blue-500/30 px-3 py-1.5 text-xs font-medium text-blue-500 hover:bg-blue-500/20 disabled:opacity-50 shadow-sm transition-colors">
                                    {acting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                                    Aprovar Todas (Rubricas)
                                </button>
                            )}
                        </div>
                        {/* Approvals List */}
                        {obj.required_teachers?.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 justify-end max-w-[50%]">
                                {obj.required_teachers.map((rt: any) => {
                                    const hasApproved = recentApprovals.some((a: any) => a.teacher_id === rt.id && a.action === "approved");
                                    return (
                                        <span key={rt.id} className={`text-[10px] rounded-md px-2 py-0.5 font-medium border ${hasApproved ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30" : "bg-red-500/5 text-red-500/60 dark:text-red-400/60 border-red-500/20"}`}>
                                            {hasApproved ? "✓" : "⏳"} {rt.name}
                                        </span>
                                    );
                                })}
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
                            <RubricsPanel objectiveId={obj.id} teacherId={teacherId} userRole={userRole} objectiveStatus={obj.status} setObjectiveRubricStatus={setRubricStatus} />
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
    const userRole = typeof window !== "undefined"
        ? JSON.parse(localStorage.getItem("sga_user") || "{}").role || ""
        : "";

    useEffect(() => {
        getDisciplines().then(r => {
            const discs = r.data || [];
            setDisciplines(discs);
            getTeacherClass().then(tc => {
                const myClasses = tc.data || [];
                if (myClasses.length > 0) {
                    const firstDiscId = myClasses[0].discipline_id || myClasses[0].discipline?.id;
                    if (firstDiscId) {
                        setSelectedDisc(String(firstDiscId));
                    } else if (discs.length > 0) {
                        setSelectedDisc(String(discs[0].id));
                    }
                } else if (discs.length > 0) {
                    setSelectedDisc(String(discs[0].id));
                }
            }).catch(() => {
                if (discs.length > 0) setSelectedDisc(String(discs[0].id));
            });
        }).catch(() => { });

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
        // Só considera "approved" pleno se não tiver pending, draft ou rejected em lugar nenhum.
        else if (allStatuses.length > 0 && allStatuses.every(s => s === "approved")) skillStatus = "approved";

        return { code, description: data.description, skillStatus, items: data.items };
    });

    const stats = {
        total: groupsArray.length,
        approved: groupsArray.filter(g => g.skillStatus === "approved").length,
        pending: groupsArray.filter(g => g.skillStatus === "pending").length,
        draft: groupsArray.filter(g => g.skillStatus === "draft").length,
    };

    // ─────────────────────────────────────────
    // LÓGICA DE AÇÕES EM LOTE
    // ─────────────────────────────────────────
    const [batchActing, setBatchActing] = useState<string | null>(null);
    const [batchEditModal, setBatchEditModal] = useState<{ isOpen: boolean; groupCode: string; items: any[] }>({ isOpen: false, groupCode: "", items: [] });
    const [batchEditValues, setBatchEditValues] = useState<Record<string, string>>({});

    const openBatchEdit = (groupCode: string, items: any[]) => {
        const initialValues: Record<string, string> = {};
        items.forEach(o => { initialValues[o.id] = o.description; });
        setBatchEditValues(initialValues);
        setBatchEditModal({ isOpen: true, groupCode, items });
    };

    const handleBatchSave = async () => {
        setBatchActing("saving_batch");
        try {
            const promessas = batchEditModal.items.map(o => {
                const newDesc = batchEditValues[o.id];
                if (newDesc !== o.description) {
                    return approveObjective(o.id, { teacher_id: teacherId, action: "edited", new_description: newDesc, notes: "Edição em lote" });
                }
                return Promise.resolve();
            });
            await Promise.all(promessas);
            setBatchEditModal({ isOpen: false, groupCode: "", items: [] });
            load();
        } catch (e: any) { alert(e?.response?.data?.detail || "Erro ao salvar em lote."); }
        finally { setBatchActing(null); }
    };

    const handleBatchApproveObjectives = async (groupCode: string, items: any[]) => {
        setBatchActing(`obj_${groupCode}`);
        try {
            const pendentes = items.filter(o => o.status === "pending" || o.status === "draft");
            await Promise.all(pendentes.map(o => approveObjective(o.id, { teacher_id: teacherId, action: "approved" })));
            load();
        } catch (e: any) { alert(e?.response?.data?.detail || "Erro ao aprovar objetivos em lote."); }
        finally { setBatchActing(null); }
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
                                    <div className="px-1 border-b pb-2 flex items-start justify-between">
                                        <div>
                                            <h3 className="text-lg font-bold flex items-center gap-3">
                                                <span className="bg-emerald-500/15 text-emerald-500 px-2.5 py-1 rounded-lg text-sm font-mono border border-emerald-500/20">{group.code}</span>
                                                <StatusBadge status={group.skillStatus} />
                                            </h3>
                                            {group.description && <p className="text-sm text-muted-foreground mt-2 leading-relaxed max-w-3xl">{group.description}</p>}
                                        </div>

                                        {/* Ações Rápidas (Batch) */}
                                        <div className="flex flex-col sm:flex-row gap-2 shrink-0">
                                            {group.items.some((o: any) => o.status !== "approved") && (
                                                <button onClick={() => openBatchEdit(group.code, group.items)}
                                                    className="bg-secondary/80 text-foreground border border-border hover:bg-secondary px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 transition-colors">
                                                    <Edit3 className="h-3.5 w-3.5" />
                                                    Editar Objetivos
                                                </button>
                                            )}
                                            {group.items.some((o: any) => o.status === "pending" || o.status === "draft") && (
                                                <button onClick={() => handleBatchApproveObjectives(group.code, group.items)} disabled={!!batchActing}
                                                    className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/30 hover:bg-emerald-500/20 px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 transition-colors">
                                                    {batchActing === `obj_${group.code}` ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                                                    Aprovar Todos (Obj)
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                    <div className="grid gap-3 border-l-2 border-emerald-500/30 pl-4 py-1">
                                        {group.items.map((o: any) => (
                                            <ObjectiveItem key={o.id} obj={o} teacherId={teacherId} userRole={userRole} onRefresh={load} />
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                );
            })()}

            {/* Modal de Edição em Lote */}
            <AnimatePresence>
                {batchEditModal.isOpen && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
                        <motion.div initial={{ scale: 0.95 }} animate={{ scale: 1 }} exit={{ scale: 0.95 }}
                            className="bg-card border border-border rounded-2xl shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
                            <div className="p-4 border-b border-border flex justify-between items-center bg-secondary/30">
                                <div>
                                    <h2 className="text-lg font-bold flex items-center gap-2">
                                        <Edit3 className="w-5 h-5 text-primary" /> Editar Objetivos em Lote
                                    </h2>
                                    <p className="text-xs text-muted-foreground mt-1">Habilidade: <span className="font-mono text-primary">{batchEditModal.groupCode}</span></p>
                                </div>
                                <button onClick={() => setBatchEditModal({ isOpen: false, groupCode: "", items: [] })} className="p-2 hover:bg-secondary rounded-full">
                                    <X className="w-5 h-5 text-muted-foreground" />
                                </button>
                            </div>
                            <div className="p-4 overflow-y-auto flex-1 space-y-4">
                                {batchEditModal.items.map((o: any) => {
                                    const lastEditIndex = o.approvals ? o.approvals.map((a: any) => a.action).lastIndexOf("edited") : -1;
                                    const lastEdit = lastEditIndex !== -1 ? o.approvals[lastEditIndex] : null;

                                    return (
                                        <div key={o.id} className="bg-secondary/20 p-3 rounded-xl border border-border">
                                            <div className="flex justify-between items-center mb-2">
                                                <span className="text-xs font-bold text-muted-foreground uppercase">Objetivo {o.order_index}</span>
                                                <StatusBadge status={o.status} />
                                            </div>
                                            {lastEdit && (
                                                <div className="mb-2 p-2 bg-background/50 rounded-lg border border-border/50">
                                                    <p className="text-[10px] text-muted-foreground uppercase font-bold flex items-center gap-1 mb-1">
                                                        <Info className="w-3 h-3" /> Modificações Anteriores ({lastEdit.teacher_name})
                                                    </p>
                                                    <DiffText oldText={lastEdit.previous_description} newText={o.description} />
                                                </div>
                                            )}
                                            <textarea
                                                className="input text-sm min-h-[80px]"
                                                value={batchEditValues[o.id]}
                                                onChange={(e) => setBatchEditValues({ ...batchEditValues, [o.id]: e.target.value })}
                                            />
                                        </div>
                                    );
                                })}
                            </div>
                            <div className="p-4 border-t border-border flex justify-end gap-3 bg-secondary/30">
                                <button onClick={() => setBatchEditModal({ isOpen: false, groupCode: "", items: [] })} disabled={batchActing === "saving_batch"}
                                    className="px-4 py-2 rounded-xl text-sm font-medium hover:bg-secondary transition-colors">
                                    Cancelar
                                </button>
                                <button onClick={handleBatchSave} disabled={batchActing === "saving_batch"}
                                    className="btn-primary flex items-center gap-2 px-6 py-2">
                                    {batchActing === "saving_batch" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                    Salvar Alterações
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
