"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen, Search, Loader2, AlertCircle, ChevronDown, ChevronRight, Target, AlignLeft, GraduationCap } from "lucide-react";
import { getDisciplines, getClassesYears, getBnccSkills, getCompetencies, getObjectives } from "@/lib/api";

export default function BnccLibraryPage() {
    const [disciplines, setDisciplines] = useState<any[]>([]);
    const [availableYears, setAvailableYears] = useState<number[]>([]);

    const [selectedDisc, setSelectedDisc] = useState<string>("");
    const [yearLevel, setYearLevel] = useState<number>(0);

    const [competencies, setCompetencies] = useState<any[]>([]);
    const [skills, setSkills] = useState<any[]>([]);
    const [objectives, setObjectives] = useState<any[]>([]);

    const [loading, setLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");

    // Accordion state
    const [expandedSkills, setExpandedSkills] = useState<Record<string, boolean>>({});

    useEffect(() => {
        getDisciplines().then(r => setDisciplines(r.data)).catch(() => { });
        getClassesYears().then(r => {
            const yList = r.data || [];
            setAvailableYears(yList);
            if (yList.length > 0) setYearLevel(yList[0]);
        }).catch(() => { });
    }, []);

    const loadLibrary = async () => {
        if (!selectedDisc) return;
        setLoading(true);
        try {
            // 1. Fetch competencies
            const compRes = await getCompetencies({ discipline_id: selectedDisc, year_grade: yearLevel });
            setCompetencies(compRes.data || []);

            // 2. Fetch skills
            const skillRes = await getBnccSkills({ discipline_id: selectedDisc, year_grade: yearLevel });
            setSkills(skillRes.data || []);

            // 3. Fetch objectives for all bimesters
            const [b1, b2, b3, b4] = await Promise.all([
                getObjectives({ discipline_id: selectedDisc, year_level: yearLevel, bimester: 1, bncc_code: "_all" }).catch(() => ({ data: [] })),
                getObjectives({ discipline_id: selectedDisc, year_level: yearLevel, bimester: 2, bncc_code: "_all" }).catch(() => ({ data: [] })),
                getObjectives({ discipline_id: selectedDisc, year_level: yearLevel, bimester: 3, bncc_code: "_all" }).catch(() => ({ data: [] })),
                getObjectives({ discipline_id: selectedDisc, year_level: yearLevel, bimester: 4, bncc_code: "_all" }).catch(() => ({ data: [] })),
            ]);

            setObjectives([...b1.data, ...b2.data, ...b3.data, ...b4.data]);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadLibrary();
    }, [selectedDisc, yearLevel]);

    const toggleSkill = (code: string) => {
        setExpandedSkills(prev => ({ ...prev, [code]: !prev[code] }));
    };

    const filteredSkills = skills.filter(skill => {
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        return (skill.bncc_code || "").toLowerCase().includes(q) ||
            (skill.description || "").toLowerCase().includes(q);
    });

    return (
        <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:px-6">
            {/* Header */}
            <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/20">
                    <BookOpen className="h-6 w-6 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Biblioteca BNCC</h1>
                    <p className="text-sm text-muted-foreground">Consulte Competências Específicas, Habilidades, Objetivos e Rubricas</p>
                </div>
            </motion.div>

            {/* Configurações de Busca */}
            <div className="flex flex-col gap-4 sm:flex-row">
                <select className="input sm:w-1/4" value={selectedDisc} onChange={e => setSelectedDisc(e.target.value)}>
                    <option value="">Disciplina...</option>
                    {disciplines.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
                <select className="input sm:w-1/4" value={yearLevel} onChange={e => setYearLevel(Number(e.target.value))}>
                    {availableYears.map(y => <option key={y} value={y}>{y}º Ano</option>)}
                </select>
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Buscar por código (Ex: EF06MA) ou descrição..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="input pl-10"
                    />
                </div>
            </div>

            {/* Listagem */}
            {!selectedDisc ? (
                <div className="flex flex-col items-center justify-center py-20 text-center text-muted-foreground bg-card/60 border border-border rounded-2xl">
                    <GraduationCap className="mb-3 h-10 w-10 opacity-30" />
                    <p className="text-base font-medium">Selecione uma disciplina para visualizar a árvore da BNCC.</p>
                </div>
            ) : loading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
            ) : (
                <div className="space-y-6">
                    {/* Competências Section */}
                    {competencies.length > 0 && !searchQuery && (
                        <div className="rounded-2xl border border-border bg-card/60 overflow-hidden">
                            <div className="bg-secondary/50 px-5 py-3 border-b border-border flex items-center gap-2">
                                <Target className="h-5 w-5 text-indigo-500" />
                                <h2 className="font-semibold text-foreground">Competências Específicas</h2>
                            </div>
                            <div className="p-5 grid gap-3">
                                {competencies.map(comp => (
                                    <div key={comp.id} className="text-sm flex gap-3 text-muted-foreground border-l-2 border-indigo-500/30 pl-3">
                                        <span className="font-bold text-foreground">C{comp.competency_number}.</span>
                                        <span className="leading-relaxed">{comp.description}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Habilidades Section */}
                    <div className="rounded-2xl border border-border bg-card/80 overflow-hidden mt-6">
                        <div className="bg-secondary/50 px-5 py-3 border-b border-border flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <AlignLeft className="h-5 w-5 text-blue-500" />
                                <h2 className="font-semibold text-foreground">Habilidades, Objetivos e Rubricas</h2>
                            </div>
                            <span className="text-xs font-semibold px-2 py-1 rounded bg-blue-500/10 text-blue-500">
                                {filteredSkills.length} listadas
                            </span>
                        </div>

                        {filteredSkills.length === 0 ? (
                            <div className="p-10 text-center text-muted-foreground text-sm">Nenhuma habilidade encontrada.</div>
                        ) : (
                            <div className="divide-y divide-border">
                                {filteredSkills.map(skill => {
                                    const isExpanded = expandedSkills[skill.bncc_code];
                                    const skillObjs = objectives.filter(o => o.bncc_code === skill.bncc_code);

                                    return (
                                        <div key={skill.bncc_code} className="transition-colors hover:bg-secondary/10">
                                            {/* Skill Header */}
                                            <div
                                                className="px-5 py-4 flex gap-4 cursor-pointer select-none"
                                                onClick={() => toggleSkill(skill.bncc_code)}
                                            >
                                                <button className="mt-0.5 shrink-0 text-muted-foreground hover:text-foreground">
                                                    {isExpanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
                                                </button>
                                                <div className="shrink-0">
                                                    <span className="rounded-lg bg-blue-500/10 px-2.5 py-1 font-mono text-sm font-bold text-blue-600 dark:text-blue-400 border border-blue-500/20 shadow-sm">
                                                        {skill.bncc_code}
                                                    </span>
                                                </div>
                                                <div className="flex-1">
                                                    <p className="text-sm leading-relaxed text-foreground ">{skill.description}</p>
                                                    <div className="mt-1.5 flex gap-2">
                                                        <span className="text-[10px] font-medium text-emerald-500 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                                                            {skillObjs.length} Objetivos
                                                        </span>
                                                        {skill.object_of_knowledge && (
                                                            <span className="text-[10px] font-medium text-muted-foreground bg-secondary px-1.5 py-0.5 rounded truncate max-w-[200px]" title={skill.object_of_knowledge}>
                                                                {skill.object_of_knowledge}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Objectives & Rubrics Body */}
                                            <AnimatePresence>
                                                {isExpanded && (
                                                    <motion.div
                                                        initial={{ height: 0, opacity: 0 }}
                                                        animate={{ height: "auto", opacity: 1 }}
                                                        exit={{ height: 0, opacity: 0 }}
                                                        className="overflow-hidden bg-background/50 border-t border-border/50"
                                                    >
                                                        <div className="p-4 pl-14 space-y-4">
                                                            {skillObjs.length === 0 ? (
                                                                <p className="text-xs text-muted-foreground">Nenhum objetivo de aprendizagem cadastrado para esta habilidade.</p>
                                                            ) : (
                                                                skillObjs.map(obj => (
                                                                    <div key={obj.id} className="rounded-xl border border-border bg-card p-4">
                                                                        <div className="flex items-start gap-3">
                                                                            <span className="mt-0.5 text-[10px] font-mono font-bold text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">Obj. {obj.order_index}</span>
                                                                            <p className="text-sm font-medium leading-relaxed flex-1">{obj.description}</p>

                                                                            <span className={`shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full border ${obj.status === 'approved' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' : 'bg-amber-500/10 text-amber-500 border-amber-500/20'}`}>
                                                                                {obj.status === 'approved' ? 'Aprovado' : 'Pendente'}
                                                                            </span>
                                                                        </div>

                                                                        {/* Simplificação das Rubricas - if obj.has_rubrics => just say it has rubrics or show a link. We don't fetch rubrics for everything to save bandwidth, but we can display the status */}
                                                                        <div className="mt-3 ml-[52px]">
                                                                            {obj.has_rubrics ? (
                                                                                <span className="text-xs font-semibold text-blue-500 flex items-center gap-1.5">
                                                                                    <AlignLeft className="h-3 w-3" /> Possui Rubricas Definidas ({obj.rubrics_status === 'approved' ? 'Aprovadas' : 'Pendentes'})
                                                                                </span>
                                                                            ) : (
                                                                                <span className="text-xs font-medium text-muted-foreground"> Sem rubricas criadas.</span>
                                                                            )}
                                                                        </div>
                                                                    </div>
                                                                ))
                                                            )}
                                                        </div>
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

