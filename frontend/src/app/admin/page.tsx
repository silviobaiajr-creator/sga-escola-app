"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    ShieldCheck, Users, BookOpen, GraduationCap, Layers,
    Plus, Pencil, Trash2, Upload, CheckCircle2, XCircle,
    AlertCircle, Loader2, Link2, ChevronDown
} from "lucide-react";
import {
    getClasses, createClass, deleteClass,
    getDisciplines, createDiscipline, deleteDiscipline,
    getUsers, createUser, toggleUserActive,
    getCompetencies, createCompetency, deleteCompetency,
    getTeacherClass, createTeacherClass, deleteTeacherClass,
    uploadStudentsCSV
} from "@/lib/api";

// ─────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────
type Tab = "turmas" | "disciplinas" | "professores" | "competencias" | "vinculos" | "csv";

const TABS: { id: Tab; label: string; icon: React.ComponentType<any> }[] = [
    { id: "turmas", label: "Turmas", icon: GraduationCap },
    { id: "disciplinas", label: "Disciplinas", icon: BookOpen },
    { id: "professores", label: "Professores", icon: Users },
    { id: "competencias", label: "Competências", icon: Layers },
    { id: "vinculos", label: "Prof. ↔ Turma", icon: Link2 },
    { id: "csv", label: "Importar CSV", icon: Upload },
];

// ─────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────
function Badge({ children, color = "blue" }: { children: React.ReactNode; color?: string }) {
    const colors: Record<string, string> = {
        blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
        green: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
        red: "bg-red-500/10 text-red-400 border-red-500/20",
        purple: "bg-purple-500/10 text-purple-400 border-purple-500/20",
        amber: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    };
    return (
        <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${colors[color]}`}>
            {children}
        </span>
    );
}

function EmptyState({ message }: { message: string }) {
    return (
        <div className="flex flex-col items-center justify-center py-16 text-center text-muted-foreground">
            <AlertCircle className="mb-3 h-10 w-10 opacity-30" />
            <p className="text-sm">{message}</p>
        </div>
    );
}

// ─────────────────────────────────────────
// ABA: TURMAS
// ─────────────────────────────────────────
function ClassesTab() {
    const [items, setItems] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [form, setForm] = useState({ class_name: "", year_level: "", shift: "morning" });
    const [saving, setSaving] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try { const r = await getClasses(); setItems(r.data); }
        catch { } finally { setLoading(false); }
    }, []);

    useEffect(() => { load(); }, [load]);

    const handleAdd = async () => {
        if (!form.class_name) return;
        setSaving(true);
        try {
            await createClass({ ...form, year_level: form.year_level ? Number(form.year_level) : null });
            setForm({ class_name: "", year_level: "", shift: "morning" });
            load();
        } catch (e: any) {
            alert(e?.response?.data?.detail || "Erro ao criar turma.");
        } finally { setSaving(false); }
    };

    const handleDelete = async (id: number, name: string) => {
        if (!confirm(`Excluir a turma "${name}"?`)) return;
        try { await deleteClass(id); load(); }
        catch (e: any) { alert(e?.response?.data?.detail || "Erro ao excluir."); }
    };

    const shiftLabel = (s: string) => ({ morning: "Manhã", afternoon: "Tarde", evening: "Noite" }[s] || s);

    return (
        <div className="space-y-6">
            {/* Form */}
            <div className="grid grid-cols-1 gap-3 rounded-2xl border border-border bg-card/60 p-4 sm:grid-cols-4">
                <input value={form.class_name} onChange={e => setForm(f => ({ ...f, class_name: e.target.value }))}
                    placeholder="Nome da turma (ex: 6A)" className="input" />
                <input value={form.year_level} onChange={e => setForm(f => ({ ...f, year_level: e.target.value }))}
                    type="number" placeholder="Ano escolar (6-9)" className="input" />
                <select value={form.shift} onChange={e => setForm(f => ({ ...f, shift: e.target.value }))} className="input">
                    <option value="morning">Manhã</option>
                    <option value="afternoon">Tarde</option>
                    <option value="evening">Noite</option>
                </select>
                <button onClick={handleAdd} disabled={saving || !form.class_name}
                    className="btn-primary flex items-center justify-center gap-2">
                    {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                    Adicionar
                </button>
            </div>

            {/* List */}
            {loading ? (
                <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
            ) : items.length === 0 ? <EmptyState message="Nenhuma turma cadastrada." /> : (
                <div className="divide-y divide-border rounded-2xl border border-border bg-card/60 overflow-hidden">
                    {items.map((item) => (
                        <div key={item.id} className="flex items-center justify-between px-4 py-3">
                            <div className="flex items-center gap-3">
                                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400">
                                    <GraduationCap className="h-4 w-4" />
                                </div>
                                <div>
                                    <p className="font-medium text-sm">{item.class_name}</p>
                                    <p className="text-xs text-muted-foreground">
                                        {item.year_level ? `${item.year_level}º Ano` : ""} · {shiftLabel(item.shift || "morning")}
                                    </p>
                                </div>
                            </div>
                            <button onClick={() => handleDelete(item.id, item.class_name)}
                                className="text-muted-foreground hover:text-red-400 transition-colors">
                                <Trash2 className="h-4 w-4" />
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// ─────────────────────────────────────────
// ABA: DISCIPLINAS
// ─────────────────────────────────────────
function DisciplinesTab() {
    const [items, setItems] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [form, setForm] = useState({ discipline_name: "", abbreviation: "", color_code: "#6366f1", area: "" });
    const [saving, setSaving] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try { const r = await getDisciplines(); setItems(r.data); }
        catch { } finally { setLoading(false); }
    }, []);
    useEffect(() => { load(); }, [load]);

    const handleAdd = async () => {
        if (!form.discipline_name) return;
        setSaving(true);
        try { await createDiscipline(form); setForm({ discipline_name: "", abbreviation: "", color_code: "#6366f1", area: "" }); load(); }
        catch (e: any) { alert(e?.response?.data?.detail || "Erro."); }
        finally { setSaving(false); }
    };

    const handleDelete = async (id: number, name: string) => {
        if (!confirm(`Excluir "${name}"?`)) return;
        try { await deleteDiscipline(id); load(); }
        catch (e: any) { alert(e?.response?.data?.detail || "Erro."); }
    };

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 gap-3 rounded-2xl border border-border bg-card/60 p-4 sm:grid-cols-2 lg:grid-cols-4">
                <input value={form.discipline_name} onChange={e => setForm(f => ({ ...f, discipline_name: e.target.value }))}
                    placeholder="Nome da disciplina" className="input lg:col-span-2" />
                <input value={form.abbreviation} onChange={e => setForm(f => ({ ...f, abbreviation: e.target.value }))}
                    placeholder="Sigla (ex: MAT)" className="input" />
                <input value={form.area} onChange={e => setForm(f => ({ ...f, area: e.target.value }))}
                    placeholder="Área (ex: Matemática)" className="input" />
                <div className="flex items-center gap-2 sm:col-span-2 lg:col-span-3">
                    <label className="text-xs text-muted-foreground">Cor:</label>
                    <input type="color" value={form.color_code} onChange={e => setForm(f => ({ ...f, color_code: e.target.value }))}
                        className="h-9 w-9 cursor-pointer rounded-lg border border-border bg-transparent" />
                    <span className="text-xs text-muted-foreground">{form.color_code}</span>
                </div>
                <button onClick={handleAdd} disabled={saving || !form.discipline_name}
                    className="btn-primary flex items-center justify-center gap-2">
                    {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                    Adicionar
                </button>
            </div>

            {loading ? <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
                : items.length === 0 ? <EmptyState message="Nenhuma disciplina cadastrada." /> : (
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                        {items.map((d) => (
                            <div key={d.id} className="flex items-center justify-between rounded-xl border border-border bg-card/60 p-3">
                                <div className="flex items-center gap-3">
                                    <div className="h-8 w-8 rounded-lg" style={{ backgroundColor: d.color_code || "#6366f1" }} />
                                    <div>
                                        <p className="text-sm font-medium">{d.name}</p>
                                        <p className="text-xs text-muted-foreground">{d.abbreviation} · {d.area || "—"}</p>
                                    </div>
                                </div>
                                <button onClick={() => handleDelete(d.id, d.name)}
                                    className="text-muted-foreground hover:text-red-400 transition-colors">
                                    <Trash2 className="h-4 w-4" />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
        </div>
    );
}

// ─────────────────────────────────────────
// ABA: PROFESSORES
// ─────────────────────────────────────────
function UsersTab() {
    const [items, setItems] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [form, setForm] = useState({ username: "", password: "", full_name: "", email: "", role: "teacher" });
    const [saving, setSaving] = useState(false);
    const [showForm, setShowForm] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        try { const r = await getUsers(); setItems(r.data); }
        catch { } finally { setLoading(false); }
    }, []);
    useEffect(() => { load(); }, [load]);

    const handleAdd = async () => {
        if (!form.username || !form.password) return;
        setSaving(true);
        try {
            await createUser(form);
            setForm({ username: "", password: "", full_name: "", email: "", role: "teacher" });
            setShowForm(false);
            load();
        } catch (e: any) { alert(e?.response?.data?.detail || "Erro."); }
        finally { setSaving(false); }
    };

    const handleToggle = async (id: string) => {
        try { await toggleUserActive(id); load(); }
        catch { }
    };

    const roleLabel = (r: string) => ({ admin: "Admin", coordinator: "Coordenador", teacher: "Professor" }[r] || r);
    const roleColor = (r: string) => ({ admin: "red", coordinator: "purple", teacher: "blue" }[r] || "blue");

    return (
        <div className="space-y-4">
            <button onClick={() => setShowForm(v => !v)}
                className="btn-primary flex items-center gap-2">
                <Plus className="h-4 w-4" />
                Novo usuário
            </button>

            <AnimatePresence>
                {showForm && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}
                        className="grid grid-cols-1 gap-3 rounded-2xl border border-border bg-card/60 p-4 sm:grid-cols-2">
                        <input value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
                            placeholder="Nome completo" className="input" />
                        <input value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                            type="email" placeholder="E-mail" className="input" />
                        <input value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                            placeholder="Usuário (login)" className="input" />
                        <input value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                            type="password" placeholder="Senha inicial" className="input" />
                        <select value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))} className="input">
                            <option value="teacher">Professor</option>
                            <option value="coordinator">Coordenador</option>
                            <option value="admin">Administrador</option>
                        </select>
                        <button onClick={handleAdd} disabled={saving}
                            className="btn-primary flex items-center justify-center gap-2">
                            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                            Salvar
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>

            {loading ? <div className="flex justify-center py-10"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
                : items.length === 0 ? <EmptyState message="Nenhum usuário." /> : (
                    <div className="divide-y divide-border rounded-2xl border border-border bg-card/60 overflow-hidden">
                        {items.map((u) => (
                            <div key={u.id} className="flex items-center justify-between px-4 py-3">
                                <div className="flex items-center gap-3">
                                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white text-sm font-bold">
                                        {(u.full_name || u.username || "?")[0].toUpperCase()}
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium">{u.full_name || u.username}</p>
                                        <p className="text-xs text-muted-foreground">{u.email || u.username}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Badge color={roleColor(u.role)}>{roleLabel(u.role)}</Badge>
                                    <button onClick={() => handleToggle(u.id)}
                                        className={`rounded-full p-1 transition-colors ${u.is_active ? "text-emerald-400 hover:text-red-400" : "text-red-400 hover:text-emerald-400"}`}>
                                        {u.is_active ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
        </div>
    );
}

// ─────────────────────────────────────────
// ABA: UPLOAD CSV
// ─────────────────────────────────────────
function CSVUploadTab() {
    const [file, setFile] = useState<File | null>(null);
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [dragOver, setDragOver] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault(); setDragOver(false);
        const f = e.dataTransfer.files?.[0];
        if (f?.name.endsWith(".csv")) setFile(f);
        else alert("Selecione um arquivo .csv");
    };

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true); setResult(null);
        try {
            const r = await uploadStudentsCSV(file);
            setResult(r.data);
        } catch (e: any) {
            setResult({ error: e?.response?.data?.detail || "Erro no upload." });
        } finally { setLoading(false); }
    };

    return (
        <div className="space-y-6">
            {/* Instrução */}
            <div className="rounded-2xl border border-blue-500/20 bg-blue-500/5 p-4">
                <p className="text-sm font-medium text-blue-400 mb-1">Formato do CSV</p>
                <p className="text-xs text-muted-foreground">
                    Colunas obrigatórias: <code className="rounded bg-secondary px-1">nome</code>,{" "}
                    <code className="rounded bg-secondary px-1">id_aluno</code>,{" "}
                    <code className="rounded bg-secondary px-1">turma</code>
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                    Colunas opcionais: <code className="rounded bg-secondary px-1">data_nascimento</code>{" "}
                    (YYYY-MM-DD), <code className="rounded bg-secondary px-1">nr_matricula</code>
                </p>
            </div>

            {/* Drop Zone */}
            <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
                className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-12 transition-all ${dragOver ? "border-primary bg-primary/5" : "border-border bg-card/40 hover:border-primary/50 hover:bg-primary/5"}`}
            >
                <input ref={inputRef} type="file" accept=".csv" className="hidden"
                    onChange={e => { const f = e.target.files?.[0]; if (f) setFile(f); }} />
                <Upload className={`mb-3 h-10 w-10 transition-colors ${file ? "text-primary" : "text-muted-foreground"}`} />
                {file ? (
                    <div className="text-center">
                        <p className="font-medium text-sm text-primary">{file.name}</p>
                        <p className="text-xs text-muted-foreground mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                ) : (
                    <div className="text-center">
                        <p className="text-sm text-muted-foreground">Arraste o arquivo CSV ou clique para selecionar</p>
                    </div>
                )}
            </div>

            {file && (
                <button onClick={handleUpload} disabled={loading}
                    className="btn-primary w-full flex items-center justify-center gap-2 py-3">
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                    {loading ? "Importando..." : "Importar Alunos"}
                </button>
            )}

            {/* Resultado */}
            {result && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                    className={`rounded-2xl border p-4 ${result.error ? "border-red-500/20 bg-red-500/5" : "border-emerald-500/20 bg-emerald-500/5"}`}>
                    {result.error ? (
                        <div className="flex items-center gap-2 text-red-400">
                            <XCircle className="h-4 w-4" /> <p className="text-sm">{result.error}</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            <div className="flex items-center gap-2 text-emerald-400">
                                <CheckCircle2 className="h-4 w-4" />
                                <p className="text-sm font-medium">Importação concluída!</p>
                            </div>
                            <div className="grid grid-cols-3 gap-2">
                                {[
                                    { label: "Inseridos", v: result.inserted, color: "emerald" },
                                    { label: "Atualizados", v: result.updated, color: "blue" },
                                    { label: "Erros", v: result.errors?.length || 0, color: "red" },
                                ].map(s => (
                                    <div key={s.label} className={`rounded-xl border border-${s.color}-500/20 bg-${s.color}-500/10 p-3 text-center`}>
                                        <p className={`text-xl font-bold text-${s.color}-400`}>{s.v}</p>
                                        <p className="text-xs text-muted-foreground">{s.label}</p>
                                    </div>
                                ))}
                            </div>
                            {result.errors?.length > 0 && (
                                <div className="mt-2 rounded-xl border border-red-500/20 bg-red-500/5 p-3">
                                    <p className="text-xs text-red-400 font-medium mb-1">Erros encontrados:</p>
                                    <ul className="space-y-1">
                                        {result.errors.map((e: string, i: number) => (
                                            <li key={i} className="text-xs text-muted-foreground">• {e}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                </motion.div>
            )}
        </div>
    );
}

// ─────────────────────────────────────────
// PÁGINA PRINCIPAL ADMIN
// ─────────────────────────────────────────
export default function AdminPage() {
    const [activeTab, setActiveTab] = useState<Tab>("turmas");

    return (
        <div className="mx-auto max-w-5xl space-y-6 px-4 py-8 sm:px-6">
            {/* Header */}
            <motion.div initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-500 to-pink-600 shadow-lg shadow-rose-500/20">
                    <ShieldCheck className="h-6 w-6 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Administração</h1>
                    <p className="text-sm text-muted-foreground">Gerencie a estrutura pedagógica da escola</p>
                </div>
            </motion.div>

            {/* Tabs */}
            <div className="flex gap-1 overflow-x-auto rounded-2xl border border-border bg-secondary/30 p-1.5">
                {TABS.map(tab => {
                    const Icon = tab.icon;
                    const active = activeTab === tab.id;
                    return (
                        <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                            className={`flex flex-shrink-0 items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition-all ${active ? "bg-card shadow text-foreground" : "text-muted-foreground hover:text-foreground"}`}>
                            <Icon className="h-4 w-4" />
                            <span className="hidden sm:inline">{tab.label}</span>
                        </button>
                    );
                })}
            </div>

            {/* Content */}
            <AnimatePresence mode="wait">
                <motion.div key={activeTab}
                    initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.15 }}
                >
                    {activeTab === "turmas" && <ClassesTab />}
                    {activeTab === "disciplinas" && <DisciplinesTab />}
                    {activeTab === "professores" && <UsersTab />}
                    {activeTab === "csv" && <CSVUploadTab />}
                    {(activeTab === "competencias" || activeTab === "vinculos") && (
                        <div className="flex flex-col items-center justify-center py-20 text-center text-muted-foreground">
                            <Layers className="mb-3 h-10 w-10 opacity-30" />
                            <p className="text-sm">Em breve: {activeTab === "competencias" ? "Gerenciar Competências Específicas" : "Vínculos Professor ↔ Turma ↔ Disciplina"}</p>
                        </div>
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}
