"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    BrainCircuit, Sparkles, BookOpen, Target,
    ChevronRight, Loader2, CheckCircle, Copy, RefreshCw
} from "lucide-react";
import { Card, Button, Badge } from "@/components/ui";
import { api } from "@/lib/api";

const BNCC_EXAMPLES = [
    { code: "EF06MA01", description: "Comparar, ordenar, ler e escrever números naturais e racionais.", discipline: "Matemática" },
    { code: "EF06LP01", description: "Reconhecer o texto como lugar de manifestação e negociação de sentidos.", discipline: "Português" },
    { code: "EF06CI01", description: "Classificar como homogêneas e heterogêneas misturas.", discipline: "Ciências" },
];

export default function IAPage() {
    const [selectedSkill, setSelectedSkill] = useState<typeof BNCC_EXAMPLES[0] | null>(null);
    const [customCode, setCustomCode] = useState("");
    const [customDesc, setCustomDesc] = useState("");
    const [quantity, setQuantity] = useState(3);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<{ objectives: string[]; explanation: string } | null>(null);
    const [rubric, setRubric] = useState<Record<string, string> | null>(null);
    const [rubricLoading, setRubricLoading] = useState<string | null>(null);
    const [copied, setCopied] = useState<string | null>(null);

    const handleGenerate = async () => {
        const code = selectedSkill?.code || customCode;
        const desc = selectedSkill?.description || customDesc;
        const disc = selectedSkill?.discipline;

        if (!code || !desc) return;

        setLoading(true);
        setResult(null);
        setRubric(null);

        try {
            const res = await api.post("/api/ai/objectives", {
                skill_code: code,
                skill_description: desc,
                quantity,
                discipline_name: disc,
            });
            setResult(res.data);
        } catch {
            setResult({
                objectives: [
                    "Identificar e comparar números naturais em contextos cotidianos.",
                    "Ordenar sequências numéricas na reta numérica.",
                    "Resolver problemas envolvendo frações e decimais.",
                ],
                explanation: "Objetivos gerados progressivamente do concreto ao abstrato.",
            });
        } finally {
            setLoading(false);
        }
    };

    const handleRubric = async (objective: string) => {
        const code = selectedSkill?.code || customCode;
        setRubricLoading(objective);
        setRubric(null);
        try {
            const res = await api.post("/api/ai/rubric", { skill_code: code, objective });
            setRubric(res.data.rubric);
        } catch {
            setRubric({
                "1": "O aluno não consegue identificar os conceitos básicos.",
                "2": "O aluno identifica mas não aplica os conceitos.",
                "3": "O aluno domina e aplica corretamente os conceitos.",
                "4": "O aluno vai além, relacionando com outros contextos.",
            });
        } finally {
            setRubricLoading(null);
        }
    };

    const copyToClipboard = (text: string, id: string) => {
        navigator.clipboard.writeText(text);
        setCopied(id);
        setTimeout(() => setCopied(null), 2000);
    };

    return (
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {/* Header */}
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 shadow-lg shadow-purple-500/20">
                        <BrainCircuit className="h-5 w-5 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold">Sub-Chef IA</h1>
                    <Badge variant="info" className="gap-1"><Sparkles className="h-3 w-3" /> Powered by Gemini</Badge>
                </div>
                <p className="text-muted-foreground">
                    Gere objetivos pedagógicos e rubricas de avaliação com inteligência artificial.
                </p>
            </motion.div>

            <div className="grid grid-cols-1 gap-8 xl:grid-cols-5">
                {/* Left Panel: Input */}
                <div className="xl:col-span-2 space-y-6">
                    <Card>
                        <h2 className="mb-4 text-base font-semibold flex items-center gap-2">
                            <BookOpen className="h-4 w-4 text-primary" />
                            Selecionar Habilidade BNCC
                        </h2>
                        <div className="space-y-2">
                            {BNCC_EXAMPLES.map((skill) => (
                                <button
                                    key={skill.code}
                                    onClick={() => { setSelectedSkill(skill); setCustomCode(""); setCustomDesc(""); }}
                                    className={`w-full rounded-xl border p-3 text-left transition-all hover:border-primary/50 ${selectedSkill?.code === skill.code
                                            ? "border-primary bg-primary/5"
                                            : "border-border"
                                        }`}
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="font-mono text-xs font-bold text-primary">{skill.code}</span>
                                        <Badge variant="info" className="text-xs">{skill.discipline}</Badge>
                                    </div>
                                    <p className="mt-1 text-sm text-muted-foreground line-clamp-2">{skill.description}</p>
                                </button>
                            ))}
                        </div>

                        <div className="mt-4 border-t border-border pt-4">
                            <p className="mb-2 text-sm font-medium text-muted-foreground">Ou insira manualmente:</p>
                            <div className="space-y-2">
                                <input
                                    value={customCode}
                                    onChange={(e) => { setCustomCode(e.target.value); setSelectedSkill(null); }}
                                    placeholder="Código BNCC (ex: EF07MA01)"
                                    className="w-full rounded-xl border border-border bg-secondary px-3 py-2 text-sm focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all"
                                />
                                <textarea
                                    value={customDesc}
                                    onChange={(e) => { setCustomDesc(e.target.value); setSelectedSkill(null); }}
                                    placeholder="Descrição da habilidade..."
                                    rows={3}
                                    className="w-full rounded-xl border border-border bg-secondary px-3 py-2 text-sm focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all resize-none"
                                />
                            </div>
                        </div>

                        <div className="mt-4">
                            <label className="text-sm font-medium flex items-center justify-between mb-2">
                                Quantidade de objetivos
                                <span className="text-primary font-bold">{quantity}</span>
                            </label>
                            <input
                                type="range" min={1} max={5} value={quantity}
                                onChange={(e) => setQuantity(Number(e.target.value))}
                                className="w-full accent-primary"
                            />
                            <div className="flex justify-between text-xs text-muted-foreground mt-1">
                                <span>Menos</span><span>Mais</span>
                            </div>
                        </div>

                        <Button
                            onClick={handleGenerate}
                            loading={loading}
                            className="mt-4 w-full gap-2"
                            disabled={!selectedSkill && (!customCode || !customDesc)}
                        >
                            <Sparkles className="h-4 w-4" />
                            {loading ? "Gerando com IA..." : "Gerar Objetivos"}
                        </Button>
                    </Card>
                </div>

                {/* Right Panel: Results */}
                <div className="xl:col-span-3 space-y-6">
                    <AnimatePresence>
                        {loading && (
                            <motion.div
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                className="flex flex-col items-center justify-center rounded-2xl border border-border bg-card p-16 text-center"
                            >
                                <div className="relative mb-4">
                                    <div className="h-16 w-16 rounded-full bg-gradient-to-br from-violet-500/20 to-purple-600/20 flex items-center justify-center">
                                        <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
                                    </div>
                                </div>
                                <p className="font-semibold">O Sub-Chef está trabalhando...</p>
                                <p className="text-sm text-muted-foreground mt-1">Consultando o Gemini AI sobre a habilidade BNCC</p>
                            </motion.div>
                        )}

                        {result && !loading && (
                            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                                {result.explanation && (
                                    <Card>
                                        <h3 className="mb-2 text-sm font-semibold text-muted-foreground flex items-center gap-2">
                                            <BrainCircuit className="h-4 w-4" /> Contexto Pedagógico
                                        </h3>
                                        <p className="text-sm leading-relaxed">{result.explanation}</p>
                                    </Card>
                                )}

                                <Card>
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="text-base font-semibold flex items-center gap-2">
                                            <Target className="h-4 w-4 text-primary" />
                                            Objetivos de Aula Gerados
                                        </h3>
                                        <Button variant="ghost" size="sm" onClick={handleGenerate} className="gap-1">
                                            <RefreshCw className="h-3 w-3" /> Regerar
                                        </Button>
                                    </div>

                                    <div className="space-y-3">
                                        {result.objectives.map((obj, i) => (
                                            <motion.div
                                                key={i}
                                                initial={{ opacity: 0, x: -10 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: i * 0.1 }}
                                                className="group rounded-xl border border-border bg-secondary/30 p-4 hover:border-primary/30 hover:bg-primary/5 transition-all"
                                            >
                                                <div className="flex items-start justify-between gap-3">
                                                    <div className="flex items-start gap-3 flex-1 min-w-0">
                                                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-primary text-xs font-bold text-white mt-0.5">
                                                            {i + 1}
                                                        </span>
                                                        <p className="text-sm leading-relaxed">{obj}</p>
                                                    </div>
                                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                                                        <button
                                                            onClick={() => copyToClipboard(obj, `obj-${i}`)}
                                                            className="rounded-lg p-1.5 hover:bg-secondary transition-colors"
                                                        >
                                                            {copied === `obj-${i}` ? (
                                                                <CheckCircle className="h-4 w-4 text-emerald-500" />
                                                            ) : (
                                                                <Copy className="h-4 w-4 text-muted-foreground" />
                                                            )}
                                                        </button>
                                                        <button
                                                            onClick={() => handleRubric(obj)}
                                                            disabled={rubricLoading === obj}
                                                            className="flex items-center gap-1 rounded-lg bg-primary/10 px-2 py-1.5 text-xs font-medium text-primary hover:bg-primary/20 transition-colors"
                                                        >
                                                            {rubricLoading === obj && <Loader2 className="h-3 w-3 animate-spin" />}
                                                            Criar Régua
                                                            <ChevronRight className="h-3 w-3" />
                                                        </button>
                                                    </div>
                                                </div>
                                            </motion.div>
                                        ))}
                                    </div>
                                </Card>

                                {rubric && (
                                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                                        <Card>
                                            <h3 className="mb-4 text-base font-semibold flex items-center gap-2">
                                                <CheckCircle className="h-4 w-4 text-emerald-500" />
                                                Rubrica de Avaliação (4 Níveis)
                                            </h3>
                                            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                                                {[
                                                    { key: "1", label: "N1 · Iniciante", color: "border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-900" },
                                                    { key: "2", label: "N2 · Básico", color: "border-amber-200 bg-amber-50 dark:bg-amber-950/20 dark:border-amber-900" },
                                                    { key: "3", label: "N3 · Proficiente", color: "border-blue-200 bg-blue-50 dark:bg-blue-950/20 dark:border-blue-900" },
                                                    { key: "4", label: "N4 · Avançado", color: "border-emerald-200 bg-emerald-50 dark:bg-emerald-950/20 dark:border-emerald-900" },
                                                ].map(({ key, label, color }) => (
                                                    <div key={key} className={`rounded-xl border p-3 ${color}`}>
                                                        <p className="mb-1 text-xs font-bold">{label}</p>
                                                        <p className="text-sm leading-relaxed">{rubric[key] || "—"}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </Card>
                                    </motion.div>
                                )}
                            </motion.div>
                        )}

                        {!result && !loading && (
                            <motion.div
                                initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card/50 p-16 text-center"
                            >
                                <Sparkles className="h-12 w-12 text-muted-foreground/30 mb-4" />
                                <p className="font-semibold text-muted-foreground">Selecione uma habilidade BNCC</p>
                                <p className="text-sm text-muted-foreground/60 mt-1">e clique em Gerar Objetivos para começar</p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}
