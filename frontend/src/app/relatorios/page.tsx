"use client";

import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
    BarChart3, TrendingUp, AlertTriangle, Users, Loader2,
    GraduationCap, Target, Sparkles, RefreshCw
} from "lucide-react";
import { getDashboardData, getClasses, getDisciplines, getStudents, getStudentEvolution } from "@/lib/api";

// ─────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────
function getLevelColor(level: number) {
    if (level <= 0) return "bg-secondary text-muted-foreground";
    if (level < 1.5) return "bg-red-500 text-white";
    if (level < 2.5) return "bg-amber-500 text-white";
    if (level < 3.5) return "bg-blue-500 text-white";
    return "bg-emerald-500 text-white";
}

function getLevelBorder(level: number) {
    if (level < 1.5) return "border-red-400 bg-red-500/10 text-red-400";
    if (level < 2.5) return "border-amber-400 bg-amber-500/10 text-amber-400";
    if (level < 3.5) return "border-blue-400 bg-blue-500/10 text-blue-400";
    return "border-emerald-400 bg-emerald-500/10 text-emerald-400";
}

// ─────────────────────────────────────────
// MINI BAR CHART (SVG nativo — sem lib)
// ─────────────────────────────────────────
function BarChart({ data }: { data: { label: string; value: number; color: string }[] }) {
    const max = Math.max(...data.map(d => d.value), 1);
    return (
        <div className="flex items-end gap-2 h-24">
            {data.map((d, i) => (
                <div key={i} className="flex flex-1 flex-col items-center gap-1">
                    <span className="text-xs font-bold text-foreground">{d.value}</span>
                    <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${(d.value / max) * 80}px` }}
                        transition={{ duration: 0.5, delay: i * 0.08 }}
                        className={`w-full rounded-t-lg ${d.color}`}
                    />
                    <span className="text-[10px] text-muted-foreground">{d.label}</span>
                </div>
            ))}
        </div>
    );
}

// ─────────────────────────────────────────
// RADAR CHART de competências (SVG puro)
// ─────────────────────────────────────────
function RadarChart({ data }: { data: { label: string; value: number }[] }) {
    const size = 140;
    const cx = size / 2;
    const cy = size / 2;
    const r = 55;
    const n = data.length;
    if (n < 3) return null;

    const angle = (i: number) => (Math.PI * 2 * i) / n - Math.PI / 2;
    const pt = (i: number, ratio: number) => ({
        x: cx + Math.cos(angle(i)) * r * ratio,
        y: cy + Math.sin(angle(i)) * r * ratio,
    });

    const gridLevels = [0.25, 0.5, 0.75, 1];
    const polygon = data.map((d, i) => pt(i, d.value / 4));
    const polyStr = polygon.map(p => `${p.x},${p.y}`).join(" ");

    return (
        <div className="flex items-center justify-center">
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="overflow-visible">
                {/* Grid circles */}
                {gridLevels.map((gl, gi) => (
                    <polygon key={gi}
                        points={data.map((_, i) => { const p = pt(i, gl); return `${p.x},${p.y}`; }).join(" ")}
                        fill="none" stroke="currentColor" strokeOpacity="0.1" strokeWidth="1"
                        className="text-foreground"
                    />
                ))}
                {/* Axes */}
                {data.map((_, i) => (
                    <line key={i} x1={cx} y1={cy} x2={pt(i, 1).x} y2={pt(i, 1).y}
                        stroke="currentColor" strokeOpacity="0.15" strokeWidth="1" className="text-foreground" />
                ))}
                {/* Data polygon */}
                <polygon points={polyStr} fill="rgb(59 130 246 / 0.2)" stroke="rgb(59 130 246)" strokeWidth="2" />
                {/* Points */}
                {polygon.map((p, i) => (
                    <circle key={i} cx={p.x} cy={p.y} r="3" fill="rgb(59 130 246)" />
                ))}
                {/* Labels */}
                {data.map((d, i) => {
                    const lp = pt(i, 1.28);
                    return (
                        <text key={i} x={lp.x} y={lp.y} textAnchor="middle" dominantBaseline="middle"
                            fontSize="7" fill="currentColor" className="text-muted-foreground">
                            {d.label.length > 8 ? d.label.slice(0, 8) + "…" : d.label}
                        </text>
                    );
                })}
            </svg>
        </div>
    );
}

// ─────────────────────────────────────────
// KPI CARD
// ─────────────────────────────────────────
function KpiCard({ label, value, sub, icon: Icon, color }: {
    label: string; value: string | number; sub?: string;
    icon: React.ComponentType<any>; color: string;
}) {
    return (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 rounded-2xl border border-border bg-card/60 p-4">
            <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl ${color}`}>
                <Icon className="h-5 w-5" />
            </div>
            <div>
                <p className="text-2xl font-bold leading-none">{value}</p>
                {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
                <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
            </div>
        </motion.div>
    );
}

// ─────────────────────────────────────────
// HEATMAP TABLE
// ─────────────────────────────────────────
function HeatmapTable({ classAvgs }: { classAvgs: any[] }) {
    if (classAvgs.length === 0) return (
        <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
            Nenhum dado de avaliação encontrado.
        </div>
    );

    return (
        <div className="overflow-x-auto rounded-xl">
            <table className="w-full text-sm">
                <thead>
                    <tr className="border-b border-border">
                        <th className="py-3 pl-4 pr-6 text-left text-xs font-medium text-muted-foreground">Turma</th>
                        <th className="px-3 py-3 text-center text-xs font-medium text-muted-foreground">Média</th>
                        <th className="px-3 py-3 text-center text-xs font-medium text-muted-foreground">N1</th>
                        <th className="px-3 py-3 text-center text-xs font-medium text-muted-foreground">N2</th>
                        <th className="px-3 py-3 text-center text-xs font-medium text-muted-foreground">N3</th>
                        <th className="px-3 py-3 text-center text-xs font-medium text-muted-foreground">N4</th>
                        <th className="px-3 py-3 text-center text-xs font-medium text-muted-foreground">Em Risco%</th>
                    </tr>
                </thead>
                <tbody>
                    {classAvgs.map((row: any, i: number) => (
                        <motion.tr key={row.class_name}
                            initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}
                            className="border-b border-border/50 hover:bg-secondary/20 transition-colors">
                            <td className="py-3 pl-4 pr-6">
                                <div className="flex items-center gap-2">
                                    <GraduationCap className="h-3.5 w-3.5 text-muted-foreground" />
                                    <span className="font-medium text-sm">{row.class_name}</span>
                                </div>
                            </td>
                            <td className="px-3 py-3 text-center">
                                <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-bold ${getLevelBorder(row.average_level)}`}>
                                    {row.average_level.toFixed(1)}
                                </span>
                            </td>
                            {[1, 2, 3, 4].map(n => (
                                <td key={n} className="px-3 py-3 text-center">
                                    <div className={`mx-auto flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold ${getLevelColor(row.level_distribution?.[String(n)] > 0 ? n : 0)}`}>
                                        {row.level_distribution?.[String(n)] || 0}
                                    </div>
                                </td>
                            ))}
                            <td className="px-3 py-3 text-center">
                                <span className={`text-xs font-medium ${row.at_risk_pct > 40 ? "text-red-400" : row.at_risk_pct > 20 ? "text-amber-400" : "text-emerald-400"}`}>
                                    {row.at_risk_pct}%
                                </span>
                            </td>
                        </motion.tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

// ─────────────────────────────────────────
// PÁGINA PRINCIPAL
// ─────────────────────────────────────────
export default function RelatoriosPage() {
    const [dashboard, setDashboard] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [disciplines, setDisciplines] = useState<any[]>([]);
    const [selectedDisc, setSelectedDisc] = useState("");
    const [selectedBim, setSelectedBim] = useState<number | undefined>(undefined);
    const [activeTab, setActiveTab] = useState<"classes" | "skills" | "radar">("classes");

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const r = await getDashboardData({
                discipline_id: selectedDisc || undefined,
                bimester: selectedBim || undefined,
            });
            setDashboard(r.data);
        } catch { } finally { setLoading(false); }
    }, [selectedDisc, selectedBim]);

    useEffect(() => {
        getDisciplines().then(r => setDisciplines(r.data)).catch(() => { });
    }, []);

    useEffect(() => { load(); }, [load]);

    const levelDist = dashboard?.level_distribution || {};
    const levelData = [
        { label: "N1 Iniciante", value: levelDist["1"] || 0, color: "bg-red-500" },
        { label: "N2 Básico", value: levelDist["2"] || 0, color: "bg-amber-500" },
        { label: "N3 Proficiente", value: levelDist["3"] || 0, color: "bg-blue-500" },
        { label: "N4 Avançado", value: levelDist["4"] || 0, color: "bg-emerald-500" },
    ];
    const totalAssessments = levelData.reduce((a, d) => a + d.value, 0);

    const summary = dashboard?.summary || {};
    const classAvgs = dashboard?.class_averages || [];
    const skillAlerts = dashboard?.skill_alerts || [];

    // Radar data: top 6 habilidades com seus níveis médios
    const radarData = skillAlerts.slice(0, 6).map((s: any) => ({
        label: s.bncc_code,
        value: s.average_level,
    }));

    return (
        <div className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6">
            {/* Header */}
            <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-violet-600 shadow-lg shadow-blue-500/20">
                        <BarChart3 className="h-6 w-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">Dashboard Pedagógico</h1>
                        <p className="text-sm text-muted-foreground">Visão geral do desempenho da escola</p>
                    </div>
                </div>
                <button onClick={load} className="btn-secondary flex items-center gap-2 py-2 px-3 text-xs">
                    <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Atualizar
                </button>
            </motion.div>

            {/* Filtros */}
            <div className="flex flex-wrap gap-3 rounded-2xl border border-border bg-card/60 p-4">
                <select className="input max-w-[180px]" value={selectedDisc} onChange={e => setSelectedDisc(e.target.value)}>
                    <option value="">Todas as disciplinas</option>
                    {disciplines.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
                <select className="input max-w-[160px]" value={selectedBim || ""} onChange={e => setSelectedBim(e.target.value ? Number(e.target.value) : undefined)}>
                    <option value="">Todos os bimestres</option>
                    {[1, 2, 3, 4].map(b => <option key={b} value={b}>{b}º Bimestre</option>)}
                </select>
            </div>

            {loading ? (
                <div className="flex h-64 items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            ) : (
                <>
                    {/* KPI Cards */}
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                        <KpiCard label="Total de Alunos" value={summary.total_students || 0} sub="ativos" icon={Users} color="bg-blue-500/10 text-blue-400" />
                        <KpiCard label="Avaliações" value={summary.total_assessments || 0} sub="registros" icon={BarChart3} color="bg-purple-500/10 text-purple-400" />
                        <KpiCard label="Obj. Aprovados" value={summary.approved_objectives || 0} sub="prontos" icon={Target} color="bg-emerald-500/10 text-emerald-400" />
                        <KpiCard label="Pendentes" value={summary.pending_approvals || 0} sub="aprovação" icon={Sparkles} color="bg-amber-500/10 text-amber-400" />
                    </div>

                    {/* Gráfico de distribuição N1-N4 + Radar */}
                    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                        {/* Barras N1-N4 */}
                        <div className="rounded-2xl border border-border bg-card/60 p-5">
                            <h2 className="mb-1 text-sm font-semibold">Distribuição de Níveis</h2>
                            <p className="mb-4 text-xs text-muted-foreground">{totalAssessments} avaliações registradas</p>
                            <BarChart data={levelData} />
                            {/* Percentuais */}
                            {totalAssessments > 0 && (
                                <div className="mt-3 grid grid-cols-4 gap-1">
                                    {levelData.map(d => (
                                        <div key={d.label} className="text-center">
                                            <p className="text-xs font-bold">{Math.round(d.value / totalAssessments * 100)}%</p>
                                            <p className="text-[9px] text-muted-foreground">{d.label.split(" ")[0]}</p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Radar de habilidades */}
                        <div className="rounded-2xl border border-border bg-card/60 p-5">
                            <h2 className="mb-1 text-sm font-semibold">Radar de Habilidades</h2>
                            <p className="mb-4 text-xs text-muted-foreground">Média por código BNCC (top 6)</p>
                            {radarData.length >= 3 ? (
                                <RadarChart data={radarData} />
                            ) : (
                                <div className="flex h-36 items-center justify-center text-xs text-muted-foreground">
                                    Dados insuficientes para o radar
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Tabs: Por Turma / Alertas de Habilidades */}
                    <div className="rounded-2xl border border-border bg-card/60 overflow-hidden">
                        <div className="flex border-b border-border">
                            {([
                                { id: "classes", label: "📊 Por Turma" },
                                { id: "skills", label: "⚠️ Alertas de Habilidades" },
                            ] as const).map(tab => (
                                <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                                    className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.id ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"}`}>
                                    {tab.label}
                                </button>
                            ))}
                        </div>

                        <div className="p-4">
                            {activeTab === "classes" && (
                                <HeatmapTable classAvgs={classAvgs} />
                            )}

                            {activeTab === "skills" && (
                                <div className="space-y-2">
                                    {skillAlerts.length === 0 ? (
                                        <p className="py-8 text-center text-sm text-muted-foreground">Nenhum alerta de habilidade.</p>
                                    ) : (
                                        skillAlerts.map((s: any, i: number) => (
                                            <motion.div key={s.bncc_code}
                                                initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.04 }}
                                                className={`flex items-center justify-between rounded-xl border px-4 py-3 ${getLevelBorder(s.average_level)}`}>
                                                <div className="flex items-center gap-2">
                                                    {s.at_risk_pct > 50 && <AlertTriangle className="h-3.5 w-3.5 text-red-400" />}
                                                    <span className="font-mono text-xs font-bold">{s.bncc_code}</span>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <span className="text-xs text-muted-foreground">{s.total} aval.</span>
                                                    <span className="text-xs font-medium">Risco: {s.at_risk_pct}%</span>
                                                    <span className="text-sm font-bold">Média: {s.average_level.toFixed(1)}</span>
                                                </div>
                                            </motion.div>
                                        ))
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
