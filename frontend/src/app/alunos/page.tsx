"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
    Users, Search, Filter, Plus, ChevronDown,
    GraduationCap, TrendingUp, AlertTriangle, CheckCircle2
} from "lucide-react";
import { Card, Button, Badge } from "@/components/ui";
import { api } from "@/lib/api";

interface Student {
    id: string;
    name: string;
    class_name: string;
}

const statusColors: Record<string, "success" | "warning" | "error" | "info"> = {
    "Proficiente": "success",
    "Em progresso": "info",
    "Em alerta": "warning",
    "Crítico": "error",
};

export default function AlunosPage() {
    const [students, setStudents] = useState<Student[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [classFilter, setClassFilter] = useState("Todas");

    useEffect(() => {
        const load = async () => {
            try {
                const res = await api.get("/api/students?limit=100");
                setStudents(res.data);
            } catch {
                // Dados de demonstração enquanto o backend não retorna
                setStudents([
                    { id: "1001", name: "Ana Beatriz Silva", class_name: "6º Ano A" },
                    { id: "1002", name: "Carlos Eduardo Souza", class_name: "6º Ano A" },
                    { id: "1003", name: "Fernanda Lima", class_name: "6º Ano B" },
                    { id: "1004", name: "João Pedro Alves", class_name: "7º Ano A" },
                    { id: "1005", name: "Maria Clara Rocha", class_name: "7º Ano A" },
                    { id: "1006", name: "Rafael Santos", class_name: "7º Ano B" },
                    { id: "1007", name: "Isabela Martins", class_name: "8º Ano A" },
                    { id: "1008", name: "Lucas Pereira", class_name: "8º Ano A" },
                ]);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    const classes = ["Todas", ...Array.from(new Set(students.map((s) => s.class_name)))];

    const filtered = students.filter((s) => {
        const matchSearch = s.name.toLowerCase().includes(search.toLowerCase()) ||
            s.id.includes(search);
        const matchClass = classFilter === "Todas" || s.class_name === classFilter;
        return matchSearch && matchClass;
    });

    const statusList = ["Proficiente", "Em progresso", "Em alerta", "Crítico"];

    return (
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
            >
                <div>
                    <h1 className="text-3xl font-bold">Alunos</h1>
                    <p className="mt-1 text-muted-foreground">
                        Gerencie e acompanhe o desempenho de {students.length} alunos
                    </p>
                </div>
                <Button className="gap-2">
                    <Plus className="h-4 w-4" />
                    Novo Aluno
                </Button>
            </motion.div>

            {/* Stats cards */}
            <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
                {[
                    { label: "Total", value: students.length, icon: Users, color: "text-blue-500 bg-blue-50 dark:bg-blue-950/30" },
                    { label: "Proficientes", value: Math.round(students.length * 0.45), icon: CheckCircle2, color: "text-emerald-500 bg-emerald-50 dark:bg-emerald-950/30" },
                    { label: "Em Progresso", value: Math.round(students.length * 0.38), icon: TrendingUp, color: "text-amber-500 bg-amber-50 dark:bg-amber-950/30" },
                    { label: "Em Alerta", value: Math.round(students.length * 0.17), icon: AlertTriangle, color: "text-red-500 bg-red-50 dark:bg-red-950/30" },
                ].map((stat, i) => (
                    <motion.div
                        key={stat.label}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: i * 0.08 }}
                    >
                        <Card className="flex items-center gap-4">
                            <div className={`rounded-xl p-2.5 ${stat.color}`}>
                                <stat.icon className="h-5 w-5" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">{stat.value}</p>
                                <p className="text-xs text-muted-foreground">{stat.label}</p>
                            </div>
                        </Card>
                    </motion.div>
                ))}
            </div>

            {/* Filters */}
            <Card className="mb-6">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                        <input
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="Buscar por nome ou matrícula..."
                            className="w-full rounded-xl border border-border bg-secondary py-2.5 pl-10 pr-4 text-sm focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all"
                        />
                    </div>
                    <div className="relative">
                        <select
                            value={classFilter}
                            onChange={(e) => setClassFilter(e.target.value)}
                            className="appearance-none rounded-xl border border-border bg-secondary py-2.5 pl-4 pr-10 text-sm focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all cursor-pointer"
                        >
                            {classes.map((c) => <option key={c} value={c}>{c}</option>)}
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                    </div>
                    <Button variant="outline" className="gap-2 shrink-0">
                        <Filter className="h-4 w-4" />
                        Filtros
                    </Button>
                </div>
            </Card>

            {/* Table */}
            <Card className="overflow-hidden p-0">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-border bg-secondary/50">
                                <th className="px-6 py-4 text-left font-medium text-muted-foreground">Aluno</th>
                                <th className="px-6 py-4 text-left font-medium text-muted-foreground">Matrícula</th>
                                <th className="px-6 py-4 text-left font-medium text-muted-foreground">Turma</th>
                                <th className="px-6 py-4 text-left font-medium text-muted-foreground">Status</th>
                                <th className="px-6 py-4 text-right font-medium text-muted-foreground">Ações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                Array.from({ length: 6 }).map((_, i) => (
                                    <tr key={i} className="border-b border-border/50">
                                        <td colSpan={5} className="px-6 py-4">
                                            <div className="h-4 animate-pulse rounded bg-secondary" />
                                        </td>
                                    </tr>
                                ))
                            ) : filtered.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground">
                                        Nenhum aluno encontrado.
                                    </td>
                                </tr>
                            ) : (
                                filtered.map((student, i) => {
                                    const status = statusList[i % statusList.length];
                                    return (
                                        <motion.tr
                                            key={student.id}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: i * 0.03 }}
                                            className="border-b border-border/50 transition-colors hover:bg-secondary/30 cursor-pointer"
                                        >
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                                                        {student.name.split(" ").map((n) => n[0]).slice(0, 2).join("")}
                                                    </div>
                                                    <span className="font-medium">{student.name}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-muted-foreground font-mono text-xs">{student.id}</td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-2">
                                                    <GraduationCap className="h-4 w-4 text-muted-foreground" />
                                                    {student.class_name}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <Badge variant={statusColors[status]}>{status}</Badge>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <Button variant="ghost" size="sm">Ver Perfil</Button>
                                            </td>
                                        </motion.tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
                <div className="border-t border-border px-6 py-4 flex items-center justify-between text-sm text-muted-foreground">
                    <span>Mostrando {filtered.length} de {students.length} alunos</span>
                    <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm">Anterior</Button>
                        <Button variant="outline" size="sm">Próximo</Button>
                    </div>
                </div>
            </Card>
        </div>
    );
}
