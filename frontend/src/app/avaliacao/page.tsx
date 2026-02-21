"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
    ClipboardCheck, ChevronDown, Save, Users,
    BookOpen, Target, CheckCircle2, Star
} from "lucide-react";
import { Card, Button, Badge } from "@/components/ui";

const CLASSES = ["6º Ano A", "6º Ano B", "7º Ano A", "7º Ano B"];
const DISCIPLINES = ["Matemática", "Português", "Ciências", "História"];
const SKILLS = {
    "Matemática": [
        { code: "EF06MA01", description: "Comparar e ordenar números naturais e racionais" },
        { code: "EF06MA03", description: "Resolver problemas envolvendo operações com números naturais" },
        { code: "EF06MA14", description: "Classificar quadriláteros em relação a lados e ângulos" },
    ],
    "Português": [
        { code: "EF06LP01", description: "Reconhecer o texto como lugar de manifestação de sentidos" },
        { code: "EF06LP05", description: "Identificar elementos da narrativa em textos literários" },
    ],
    "Ciências": [
        { code: "EF06CI01", description: "Classificar misturas como homogêneas e heterogêneas" },
        { code: "EF06CI02", description: "Identificar evidências de transformações químicas" },
    ],
    "História": [
        { code: "EF06HI01", description: "Identificar diferentes formas de compreensão da noção de tempo e periodização" },
    ],
} as Record<string, { code: string; description: string }[]>;

const MOCK_STUDENTS = [
    "Ana Beatriz Silva", "Carlos Eduardo Souza", "Fernanda Lima",
    "João Pedro Alves", "Maria Clara Rocha", "Rafael Santos",
    "Isabela Martins", "Lucas Pereira", "Gabriela Costa", "Thiago Oliveira",
];

const LEVELS = [
    { value: 1, label: "N1 · Iniciante", color: "bg-red-500", border: "border-red-300" },
    { value: 2, label: "N2 · Básico", color: "bg-amber-500", border: "border-amber-300" },
    { value: 3, label: "N3 · Proficiente", color: "bg-blue-500", border: "border-blue-300" },
    { value: 4, label: "N4 · Avançado", color: "bg-emerald-500", border: "border-emerald-300" },
];

export default function AvaliacaoPage() {
    const [selectedClass, setSelectedClass] = useState<string>("");
    const [selectedDiscipline, setSelectedDiscipline] = useState<string>("");
    const [selectedSkill, setSelectedSkill] = useState<{ code: string; description: string } | null>(null);
    const [grades, setGrades] = useState<Record<string, number>>({});
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    const setGrade = (student: string, level: number) => {
        setGrades((prev) => ({ ...prev, [student]: level }));
    };

    const handleSave = async () => {
        setSaving(true);
        await new Promise((r) => setTimeout(r, 1200));
        setSaving(false);
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
    };

    const gradedCount = Object.keys(grades).length;
    const progress = MOCK_STUDENTS.length > 0 ? (gradedCount / MOCK_STUDENTS.length) * 100 : 0;
    const avgLevel = gradedCount > 0
        ? Object.values(grades).reduce((a, b) => a + b, 0) / gradedCount
        : 0;

    return (
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {/* Header */}
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
                <h1 className="text-3xl font-bold">Avaliação Contínua</h1>
                <p className="mt-1 text-muted-foreground">
                    Registre o nível de desempenho por habilidade BNCC em tempo real
                </p>
            </motion.div>

            {/* Step Navigation */}
            <div className="mb-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
                {/* Step 1: Select Class & Discipline */}
                <Card className="space-y-4">
                    <h2 className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-white">1</span>
                        Turma e Disciplina
                    </h2>

                    <div className="space-y-3">
                        <div>
                            <label className="mb-1 block text-xs font-medium text-muted-foreground">Turma</label>
                            <div className="relative">
                                <select
                                    value={selectedClass}
                                    onChange={(e) => setSelectedClass(e.target.value)}
                                    className="w-full appearance-none rounded-xl border border-border bg-secondary py-2.5 pl-4 pr-10 text-sm focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all cursor-pointer"
                                >
                                    <option value="">Selecione a turma…</option>
                                    {CLASSES.map((c) => <option key={c} value={c}>{c}</option>)}
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                            </div>
                        </div>

                        <div>
                            <label className="mb-1 block text-xs font-medium text-muted-foreground">Disciplina</label>
                            <div className="relative">
                                <select
                                    value={selectedDiscipline}
                                    onChange={(e) => { setSelectedDiscipline(e.target.value); setSelectedSkill(null); }}
                                    className="w-full appearance-none rounded-xl border border-border bg-secondary py-2.5 pl-4 pr-10 text-sm focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all cursor-pointer"
                                >
                                    <option value="">Selecione a disciplina…</option>
                                    {DISCIPLINES.map((d) => <option key={d} value={d}>{d}</option>)}
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
                            </div>
                        </div>
                    </div>
                </Card>

                {/* Step 2: Select Skill */}
                <Card className="space-y-4">
                    <h2 className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-white">2</span>
                        Habilidade BNCC
                    </h2>

                    {!selectedDiscipline ? (
                        <div className="flex h-24 items-center justify-center rounded-xl bg-secondary text-sm text-muted-foreground">
                            Selecione uma disciplina primeiro
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {(SKILLS[selectedDiscipline] || []).map((skill) => (
                                <button
                                    key={skill.code}
                                    onClick={() => setSelectedSkill(skill)}
                                    className={`w-full rounded-xl border p-3 text-left transition-all ${selectedSkill?.code === skill.code
                                            ? "border-primary bg-primary/5 text-primary"
                                            : "border-border hover:border-primary/30"
                                        }`}
                                >
                                    <p className="font-mono text-xs font-bold">{skill.code}</p>
                                    <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">{skill.description}</p>
                                </button>
                            ))}
                        </div>
                    )}
                </Card>

                {/* Step 3: Progress Summary */}
                <Card className="space-y-4">
                    <h2 className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-white">3</span>
                        Resumo
                    </h2>

                    <div className="space-y-4">
                        <div>
                            <div className="mb-1 flex justify-between text-xs text-muted-foreground">
                                <span>Progresso</span>
                                <span>{gradedCount}/{MOCK_STUDENTS.length} alunos</span>
                            </div>
                            <div className="h-2 overflow-hidden rounded-full bg-secondary">
                                <motion.div
                                    className="h-full rounded-full bg-primary"
                                    animate={{ width: `${progress}%` }}
                                    transition={{ duration: 0.5 }}
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                            <div className="rounded-xl bg-secondary p-3 text-center">
                                <p className="text-2xl font-bold">{gradedCount}</p>
                                <p className="text-xs text-muted-foreground">Avaliados</p>
                            </div>
                            <div className="rounded-xl bg-secondary p-3 text-center">
                                <p className="text-2xl font-bold text-primary">{avgLevel.toFixed(1)}</p>
                                <p className="text-xs text-muted-foreground">Nível médio</p>
                            </div>
                        </div>

                        <Button
                            onClick={handleSave}
                            loading={saving}
                            disabled={!selectedClass || !selectedSkill || gradedCount === 0}
                            className="w-full gap-2"
                            variant={saved ? "outline" : "default"}
                        >
                            {saved ? (
                                <><CheckCircle2 className="h-4 w-4 text-emerald-500" /> Salvo!</>
                            ) : (
                                <><Save className="h-4 w-4" /> Salvar Avaliações</>
                            )}
                        </Button>
                    </div>
                </Card>
            </div>

            {/* Student Grid */}
            {selectedClass && selectedSkill ? (
                <Card className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="flex items-center gap-2 font-semibold">
                            <Users className="h-4 w-4 text-primary" />
                            Alunos — {selectedClass}
                        </h2>
                        <Badge variant="info">{selectedSkill.code}</Badge>
                    </div>

                    {/* Level legend */}
                    <div className="flex flex-wrap gap-2">
                        {LEVELS.map((l) => (
                            <div key={l.value} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                                <div className={`h-2.5 w-2.5 rounded-sm ${l.color}`} />
                                {l.label}
                            </div>
                        ))}
                    </div>

                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                        {MOCK_STUDENTS.map((student, i) => {
                            const assigned = grades[student];
                            return (
                                <motion.div
                                    key={student}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.05 }}
                                    className={`rounded-xl border-2 p-4 transition-all ${assigned
                                            ? LEVELS[assigned - 1].border
                                            : "border-border"
                                        }`}
                                >
                                    <div className="mb-3 flex items-center gap-3">
                                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                                            {student.split(" ").map((n) => n[0]).slice(0, 2).join("")}
                                        </div>
                                        <div className="min-w-0">
                                            <p className="truncate text-sm font-medium">{student}</p>
                                            {assigned && (
                                                <p className={`text-xs font-medium ${assigned === 4 ? "text-emerald-500" :
                                                        assigned === 3 ? "text-blue-500" :
                                                            assigned === 2 ? "text-amber-500" : "text-red-500"
                                                    }`}>
                                                    {LEVELS[assigned - 1].label}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-4 gap-1.5">
                                        {LEVELS.map((level) => (
                                            <button
                                                key={level.value}
                                                onClick={() => setGrade(student, level.value)}
                                                className={`flex flex-col items-center rounded-lg py-2 text-xs font-bold text-white transition-all hover:scale-105 active:scale-95 ${level.color} ${assigned === level.value ? "ring-2 ring-white ring-offset-2 ring-offset-card" : "opacity-60 hover:opacity-100"
                                                    }`}
                                            >
                                                <Star className="mb-0.5 h-3 w-3" />
                                                {level.value}
                                            </button>
                                        ))}
                                    </div>
                                </motion.div>
                            );
                        })}
                    </div>
                </Card>
            ) : (
                <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border p-16 text-center">
                    <ClipboardCheck className="mb-4 h-12 w-12 text-muted-foreground/30" />
                    <p className="font-semibold text-muted-foreground">Configure a avaliação acima</p>
                    <p className="mt-1 text-sm text-muted-foreground/60">
                        Selecione turma, disciplina e habilidade para começar a registrar
                    </p>
                </div>
            )}
        </div>
    );
}
