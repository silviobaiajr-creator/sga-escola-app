"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { GraduationCap, Eye, EyeOff, Lock, User, Sparkles } from "lucide-react";
import { Button } from "@/components/ui";

export default function LoginPage() {
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [form, setForm] = useState({ username: "", password: "" });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        // TODO: Integrar com API de autenticação
        await new Promise((res) => setTimeout(res, 1500));
        setLoading(false);
    };

    return (
        <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-neutral-950">
            {/* Animated Background Blobs */}
            <div className="absolute inset-0 overflow-hidden">
                <motion.div
                    animate={{ scale: [1, 1.2, 1], rotate: [0, 90, 0] }}
                    transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                    className="absolute -left-40 -top-40 h-96 w-96 rounded-full bg-blue-600/20 blur-[120px]"
                />
                <motion.div
                    animate={{ scale: [1.2, 1, 1.2], rotate: [0, -90, 0] }}
                    transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
                    className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-purple-600/20 blur-[120px]"
                />
                <motion.div
                    animate={{ scale: [1, 1.3, 1], x: [0, 50, 0] }}
                    transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                    className="absolute top-1/2 left-1/2 h-64 w-64 rounded-full bg-primary/10 blur-[100px]"
                />
            </div>

            {/* Grid pattern overlay */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:14px_24px]" />

            <motion.div
                initial={{ opacity: 0, y: 30, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="relative z-10 w-full max-w-md px-4"
            >
                {/* Card */}
                <div className="rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-2xl">
                    {/* Logo */}
                    <div className="mb-8 flex flex-col items-center gap-3">
                        <div className="relative">
                            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary shadow-2xl shadow-primary/40">
                                <GraduationCap className="h-8 w-8 text-white" />
                            </div>
                            <div className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-amber-400">
                                <Sparkles className="h-3 w-3 text-amber-900" />
                            </div>
                        </div>
                        <div className="text-center">
                            <h1 className="text-2xl font-bold text-white">SGA-H Escola</h1>
                            <p className="mt-1 text-sm text-neutral-400">Gestão de Aprendizagem Inteligente</p>
                        </div>
                    </div>

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Username */}
                        <div className="space-y-1">
                            <label className="text-sm font-medium text-neutral-300">Usuário / CPF</label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500" />
                                <input
                                    type="text"
                                    value={form.username}
                                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                                    placeholder="Digite seu usuário"
                                    className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-10 pr-4 text-white placeholder-neutral-500 focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div className="space-y-1">
                            <label className="text-sm font-medium text-neutral-300">Senha</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-500" />
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={form.password}
                                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                                    placeholder="••••••••"
                                    className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-10 pr-12 text-white placeholder-neutral-500 focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300 transition-colors"
                                >
                                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>
                        </div>

                        {/* Submit */}
                        <Button
                            type="submit"
                            size="lg"
                            loading={loading}
                            className="mt-6 w-full rounded-xl bg-primary shadow-xl shadow-primary/30 text-white hover:scale-[1.02] active:scale-[0.98]"
                        >
                            {loading ? "Autenticando..." : "Entrar no Sistema"}
                        </Button>
                    </form>

                    {/* Footer */}
                    <p className="mt-6 text-center text-xs text-neutral-600">
                        SGA-H v2.0 · Powered by Google Vertex AI
                    </p>
                </div>
            </motion.div>
        </div>
    );
}
