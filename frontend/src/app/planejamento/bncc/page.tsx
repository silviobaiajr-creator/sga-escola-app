"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { BookOpen, Search, Filter, Loader2, AlertCircle } from "lucide-react";
import { getBnccSkills } from "@/lib/api";

export default function BnccLibraryPage() {
    const [skills, setSkills] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedYear, setSelectedYear] = useState<string>("");

    useEffect(() => {
        setLoading(true);
        getBnccSkills()
            .then(res => setSkills(res.data))
            .catch(err => console.error(err))
            .finally(() => setLoading(false));
    }, []);

    const filteredSkills = skills.filter(skill => {
        const matchesSearch =
            skill.bncc_code.toLowerCase().includes(searchQuery.toLowerCase()) ||
            skill.skill_description.toLowerCase().includes(searchQuery.toLowerCase());

        const matchesYear = selectedYear ? skill.year_level === Number(selectedYear) : true;

        return matchesSearch && matchesYear;
    });

    // Extract unique years for the filter
    const availableYears = Array.from(new Set(skills.map(s => s.year_level).filter(Boolean))).sort();

    return (
        <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:px-6">
            {/* Header */}
            <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/20">
                    <BookOpen className="h-6 w-6 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Biblioteca BNCC</h1>
                    <p className="text-sm text-muted-foreground">Consulte as habilidades cadastradas no sistema</p>
                </div>
            </motion.div>

            {/* Configurações de Busca */}
            <div className="flex flex-col gap-4 sm:flex-row">
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
                <div className="relative min-w-[200px]">
                    <Filter className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <select
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(e.target.value)}
                        className="input pl-10 appearance-none bg-secondary/50 focus:bg-background"
                    >
                        <option value="">Todos os anos</option>
                        {availableYears.map(year => (
                            <option key={year} value={year}>{year}º Ano</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Listagem */}
            {loading ? (
                <div className="flex justify-center py-20">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
            ) : filteredSkills.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center text-muted-foreground bg-card/60 border border-border rounded-2xl">
                    <AlertCircle className="mb-3 h-10 w-10 opacity-30" />
                    <p className="text-base font-medium">Nenhuma habilidade encontrada.</p>
                    <p className="text-sm mt-1">Lembre-se de importar o arquivo CSV na aba de Administração.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    <p className="text-sm text-muted-foreground mb-1">
                        Exibindo {filteredSkills.length} habilidade(s)
                    </p>
                    {filteredSkills.map(skill => (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            key={skill.bncc_code}
                            className="flex flex-col sm:flex-row gap-4 rounded-2xl border border-border bg-card/60 p-5 hover:bg-card hover:border-border/80 transition-all"
                        >
                            <div className="shrink-0 flex items-start gap-3">
                                <div className="rounded-lg bg-primary/10 px-3 py-1.5 font-mono text-sm font-bold text-primary border border-primary/20 shadow-sm">
                                    {skill.bncc_code}
                                </div>
                                <div className="rounded-lg bg-secondary px-3 py-1.5 text-xs font-semibold text-muted-foreground border border-border">
                                    {skill.year_level}º Ano
                                </div>
                            </div>
                            <div className="flex-1">
                                <p className="text-sm leading-relaxed text-foreground/90">{skill.skill_description}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}
        </div>
    );
}
