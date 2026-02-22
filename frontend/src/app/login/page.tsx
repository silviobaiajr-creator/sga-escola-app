"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import {
    GraduationCap, Eye, EyeOff, Lock, User, Sparkles, AlertCircle, Loader2
} from "lucide-react";
import { useAuth } from "@/lib/useAuth";

// ─────────────────────────────────────────
// Componente interno (usa useSearchParams — necessita Suspense)
// ─────────────────────────────────────────
function LoginForm() {
    const { login, isLoading: authLoading } = useAuth();
    const searchParams = useSearchParams();

    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [form, setForm] = useState({ username: "", password: "" });

    const nextPath = searchParams.get("next") || "/";

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!form.username || !form.password) {
            setError("Preencha usuário e senha.");
            return;
        }
        setError("");
        setLoading(true);
        try {
            await login(form.username, form.password);
            // useAuth já redireciona para nextPath internamente
        } catch (err: any) {
            const msg = err?.response?.data?.detail;
            setError(
                msg === "Incorrect username or password"
                    ? "Usuário ou senha incorretos."
                    : msg || "Erro ao conectar com o servidor."
            );
        } finally {
            setLoading(false);
        }
    };

    const isSubmitting = loading || authLoading;

    return (
        <motion.form
            onSubmit={handleSubmit}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="relative z-10 w-full max-w-sm space-y-5 rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-2xl"
        >
            {/* Logo */}
            <div className="text-center">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-violet-600 shadow-xl shadow-blue-500/30">
                    <GraduationCap className="h-7 w-7 text-white" />
                </div>
                <h1 className="text-2xl font-bold text-white">SGA-H Escola</h1>
                <p className="mt-1 text-sm text-white/40">Sistema de Gestão de Aprendizagem</p>
                <div className="mt-3 inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/50">
                    <Sparkles className="h-3 w-3 text-amber-400" />
                    Powered by Google Vertex AI
                </div>
            </div>

            {/* Error */}
            {error && (
                <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2.5 text-sm text-red-300"
                >
                    <AlertCircle className="h-4 w-4 flex-shrink-0" />
                    {error}
                </motion.div>
            )}

            {/* Usuário */}
            <div className="relative">
                <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                <input
                    id="username"
                    autoComplete="username"
                    value={form.username}
                    onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                    placeholder="Usuário"
                    className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-10 pr-4 text-sm text-white placeholder-white/30 outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/20"
                />
            </div>

            {/* Senha */}
            <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
                <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    value={form.password}
                    onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                    placeholder="Senha"
                    className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-10 pr-10 text-sm text-white placeholder-white/30 outline-none transition focus:border-primary/60 focus:ring-2 focus:ring-primary/20"
                />
                <button
                    type="button"
                    onClick={() => setShowPassword(v => !v)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
            </div>

            {/* Submit */}
            <button
                type="submit"
                disabled={isSubmitting}
                className="w-full rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-500/30 transition-all hover:opacity-90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 flex items-center justify-center gap-2"
            >
                {isSubmitting ? (
                    <><Loader2 className="h-4 w-4 animate-spin" /> Entrando...</>
                ) : (
                    "Entrar"
                )}
            </button>

            <p className="text-center text-xs text-white/25">
                Acesso restrito a membros da equipe escolar
            </p>
        </motion.form>
    );
}

// ─────────────────────────────────────────
// Página principal (blobs animados + fundo)
// ─────────────────────────────────────────
export default function LoginPage() {
    return (
        <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-neutral-950 px-4">
            {/* Animated Background Blobs */}
            <div className="pointer-events-none absolute inset-0">
                <motion.div
                    animate={{ scale: [1, 1.2, 1], rotate: [0, 90, 0] }}
                    transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                    className="absolute -left-40 -top-40 h-80 w-80 rounded-full bg-blue-600/20 blur-[120px]"
                />
                <motion.div
                    animate={{ scale: [1.2, 1, 1.2], rotate: [0, -90, 0] }}
                    transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
                    className="absolute -bottom-40 -right-40 h-80 w-80 rounded-full bg-purple-600/20 blur-[120px]"
                />
                <motion.div
                    animate={{ scale: [1, 1.3, 1], x: [0, 40, 0] }}
                    transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                    className="absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/10 blur-[100px]"
                />
            </div>

            {/* Form envolto em Suspense (SSR) */}
            <Suspense fallback={
                <div className="flex items-center justify-center">
                    <Loader2 className="h-8 w-8 animate-spin text-white/40" />
                </div>
            }>
                <LoginForm />
            </Suspense>
        </div>
    );
}
