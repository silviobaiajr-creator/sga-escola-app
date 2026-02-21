"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp, TrendingDown, Minus, AlertTriangle, Users } from "lucide-react";
import { Card, Badge } from "@/components/ui";
import { cn } from "@/lib/utils";

// Heatmap color based on level (0-4)
function getLevelColor(level: number) {
    if (level === 0) return "bg-secondary text-muted-foreground";
    if (level < 1.5) return "bg-red-500 text-white";
    if (level < 2.5) return "bg-amber-400 text-white";
    if (level < 3.5) return "bg-blue-500 text-white";
    return "bg-emerald-500 text-white";
}

function getLevelBadge(avg: number): "error" | "warning" | "info" | "success" {
    if (avg < 1.5) return "error";
    if (avg < 2.5) return "warning";
    if (avg < 3.5) return "info";
    return "success";
}

// Mock data - will be replaced with real API data
const MOCK_HEATMAP = {
    students: ["Ana B.", "Carlos E.", "Fernanda L.", "João P.", "Maria C.", "Rafael S.", "Isabela M.", "Lucas P.", "Gabriela C.", "Thiago O."],
    skills: ["EF06MA01", "EF06MA03", "EF06MA14", "EF06MA17", "EF06MA20"],
    data: [
        [4, 3, 4, 2, 3],
        [2, 2, 3, 1, 2],
        [3, 4, 3, 4, 4],
        [1, 1, 2, 1, 1],
        [4, 4, 4, 3, 4],
        [3, 3, 2, 3, 3],
        [2, 3, 3, 2, 3],
        [4, 4, 4, 4, 4],
        [1, 2, 1, 2, 1],
        [3, 3, 4, 3, 3],
    ],
};

export default function RelatoriosPage() {
    const [selectedClass, setSelectedClass] = useState("6º Ano A");
    const classes = ["6º Ano A", "6º Ano B", "7º Ano A", "7º Ano B"];

    const { students, skills, data } = MOCK_HEATMAP;

    // Calculate averages
    const studentAvgs = data.map((row) => row.reduce((a, b) => a + b, 0) / row.length);
    const skillAvgs = skills.map((_, si) => data.reduce((sum, row) => sum + row[si], 0) / data.length);
    const classAvg = studentAvgs.reduce((a, b) => a + b, 0) / studentAvgs.length;

    const atRisk = students.filter((_, i) => studentAvgs[i] < 2).length;
    const proficient = students.filter((_, i) => studentAvgs[i] >= 3).length;

    return (
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {/* Header */}
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Relatórios e Heatmap</h1>
                        <p className="mt-1 text-muted-foreground">
                            Diagnóstico visual de aprendizagem por turma
                        </p>
                    </div>
                    <div className="relative">
                        <select
                            value={selectedClass}
                            onChange={(e) => setSelectedClass(e.target.value)}
                            className="appearance-none rounded-xl border border-border bg-secondary py-2.5 pl-4 pr-10 text-sm font-medium focus:border-primary/50 focus:outline-none cursor-pointer"
                        >
                            {classes.map((c) => <option key={c} value={c}>{c}</option>)}
                        </select>
                    </div>
                </div>
            </motion.div>

            {/* KPI Cards */}
            <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
                {[
                    { label: "Média da Turma", value: classAvg.toFixed(1), icon: BarChart3, color: "text-purple-500 bg-purple-50 dark:bg-purple-950/30", suffix: "/4" },
                    { label: "Proficientes", value: proficient, icon: TrendingUp, color: "text-emerald-500 bg-emerald-50 dark:bg-emerald-950/30", suffix: ` alunos` },
                    { label: "Em Alerta", value: atRisk, icon: AlertTriangle, color: "text-red-500 bg-red-50 dark:bg-red-950/30", suffix: " alunos" },
                    { label: "Total", value: students.length, icon: Users, color: "text-blue-500 bg-blue-50 dark:bg-blue-950/30", suffix: " alunos" },
                ].map((kpi, i) => (
                    <motion.div
                        key={kpi.label}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: i * 0.07 }}
                    >
                        <Card className="flex items-center gap-4">
                            <div className={`rounded-xl p-2.5 ${kpi.color}`}>
                                <kpi.icon className="h-5 w-5" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">{kpi.value}<span className="text-sm font-normal text-muted-foreground">{kpi.suffix}</span></p>
                                <p className="text-xs text-muted-foreground">{kpi.label}</p>
                            </div>
                        </Card>
                    </motion.div>
                ))}
            </div>

            {/* Heatmap */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
                <Card className="overflow-hidden p-0">
                    <div className="flex items-center justify-between border-b border-border px-6 py-4">
                        <h2 className="font-semibold">Mapa de Calor — Desempenho por Habilidade</h2>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                            {[
                                { color: "bg-red-500", label: "Crítico" },
                                { color: "bg-amber-400", label: "Básico" },
                                { color: "bg-blue-500", label: "Proficiente" },
                                { color: "bg-emerald-500", label: "Avançado" },
                            ].map(({ color, label }) => (
                                <div key={label} className="flex items-center gap-1">
                                    <div className={`h-3 w-3 rounded-sm ${color}`} />
                                    <span>{label}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border">
                                    <th className="sticky left-0 z-10 bg-card px-6 py-3 text-left text-xs font-medium text-muted-foreground min-w-[140px]">
                                        Aluno
                                    </th>
                                    {skills.map((skill) => (
                                        <th key={skill} className="px-3 py-3 text-center text-xs font-mono font-medium text-muted-foreground whitespace-nowrap">
                                            {skill}
                                        </th>
                                    ))}
                                    <th className="px-4 py-3 text-center text-xs font-medium text-muted-foreground">Média</th>
                                    <th className="px-4 py-3 text-center text-xs font-medium text-muted-foreground">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {students.map((student, si) => {
                                    const avg = studentAvgs[si];
                                    return (
                                        <motion.tr
                                            key={student}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: si * 0.04 }}
                                            className="border-b border-border/50 hover:bg-secondary/20 transition-colors"
                                        >
                                            <td className="sticky left-0 z-10 bg-card px-6 py-3 hover:bg-secondary/20">
                                                <div className="flex items-center gap-2">
                                                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                                                        {student.replace(".", "").split(" ").map((n) => n[0]).join("")}
                                                    </div>
                                                    <span className="font-medium whitespace-nowrap">{student}</span>
                                                </div>
                                            </td>
                                            {data[si].map((level, ki) => (
                                                <td key={ki} className="px-3 py-3 text-center">
                                                    <div className={cn(
                                                        "mx-auto flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold",
                                                        getLevelColor(level)
                                                    )}>
                                                        {level > 0 ? level : "—"}
                                                    </div>
                                                </td>
                                            ))}
                                            <td className="px-4 py-3 text-center">
                                                <span className="text-sm font-bold">{avg.toFixed(1)}</span>
                                            </td>
                                            <td className="px-4 py-3 text-center">
                                                <Badge variant={getLevelBadge(avg)}>
                                                    {avg < 1.5 ? "Crítico" : avg < 2.5 ? "Básico" : avg < 3.5 ? "Proficiente" : "Avançado"}
                                                </Badge>
                                            </td>
                                        </motion.tr>
                                    );
                                })}
                            </tbody>
                            {/* Skill averages row */}
                            <tfoot>
                                <tr className="border-t-2 border-border bg-secondary/30">
                                    <td className="sticky left-0 z-10 bg-secondary/30 px-6 py-3 text-xs font-bold text-muted-foreground">
                                        Média por habilidade
                                    </td>
                                    {skillAvgs.map((avg, i) => (
                                        <td key={i} className="px-3 py-3 text-center">
                                            <div className={cn(
                                                "mx-auto flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold",
                                                getLevelColor(avg)
                                            )}>
                                                {avg.toFixed(1)}
                                            </div>
                                        </td>
                                    ))}
                                    <td colSpan={2} className="px-4 py-3 text-center">
                                        <span className="text-sm font-bold text-primary">{classAvg.toFixed(1)}</span>
                                    </td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </Card>
            </motion.div>

            {/* Bottom insight */}
            {atRisk > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="mt-6 flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-950/20"
                >
                    <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
                    <div>
                        <p className="font-semibold text-red-700 dark:text-red-400">
                            {atRisk} {atRisk === 1 ? "aluno precisa" : "alunos precisam"} de atenção especial
                        </p>
                        <p className="text-sm text-red-600/80 dark:text-red-400/70">
                            {students.filter((_, i) => studentAvgs[i] < 2).join(", ")} apresentam nível médio abaixo de 2,0 nas habilidades avaliadas.
                        </p>
                    </div>
                </motion.div>
            )}
        </div>
    );
}
