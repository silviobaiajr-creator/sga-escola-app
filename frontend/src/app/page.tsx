"use client";

import { motion } from "framer-motion";
import {
  ArrowUpRight, Users, GraduationCap, ClipboardCheck, Sparkles,
  LayoutDashboard, BarChart3, TrendingUp, AlertTriangle, BookOpen
} from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";

const stats = [
  { name: "Total de Alunos", value: "150", icon: Users, color: "bg-blue-500", trend: "+4% este mês", href: "/alunos" },
  { name: "Turmas Ativas", value: "6", icon: GraduationCap, color: "bg-purple-500", trend: "Em dia", href: "/relatorios" },
  { name: "Avaliações", value: "1.2k", icon: ClipboardCheck, color: "bg-emerald-500", trend: "Nesta semana", href: "/avaliacao" },
  { name: "IA Insights", value: "48", icon: Sparkles, color: "bg-amber-500", trend: "Novas rubricas", href: "/ia" },
];

const quickActions = [
  { name: "Nova Avaliação", href: "/avaliacao", icon: ClipboardCheck, color: "bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-950/30 dark:text-emerald-400 dark:hover:bg-emerald-950/50" },
  { name: "Gerar com IA", href: "/ia", icon: Sparkles, color: "bg-violet-50 text-violet-700 hover:bg-violet-100 dark:bg-violet-950/30 dark:text-violet-400 dark:hover:bg-violet-950/50" },
  { name: "Ver Heatmap", href: "/relatorios", icon: BarChart3, color: "bg-blue-50 text-blue-700 hover:bg-blue-100 dark:bg-blue-950/30 dark:text-blue-400 dark:hover:bg-blue-950/50" },
  { name: "Alunos", href: "/alunos", icon: Users, color: "bg-orange-50 text-orange-700 hover:bg-orange-100 dark:bg-orange-950/30 dark:text-orange-400 dark:hover:bg-orange-950/50" },
];

export default function Home() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Hero Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative mb-10 overflow-hidden rounded-3xl bg-gradient-to-br from-neutral-900 to-neutral-800 px-8 py-10 text-white"
      >
        <div className="relative z-10 max-w-2xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs backdrop-blur">
            <Sparkles className="h-3 w-3 text-amber-400" />
            <span>Powered by Google Vertex AI</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Bem-vindo ao <span className="bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">SGA-H Escola</span>
          </h1>
          <p className="mt-3 text-base text-neutral-400 sm:text-lg">
            Gestão de aprendizagem por habilidades com IA. Monitore, avalie e melhore o desempenho da sua escola.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/avaliacao"
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-primary/30 transition-all hover:scale-105 active:scale-95"
            >
              <ClipboardCheck className="h-4 w-4" />
              Nova Avaliação
            </Link>
            <Link
              href="/relatorios"
              className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-5 py-2.5 text-sm font-semibold backdrop-blur-sm transition-all hover:bg-white/10"
            >
              <BarChart3 className="h-4 w-4" />
              Ver Relatórios
            </Link>
          </div>
        </div>
        {/* Decorative */}
        <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-primary/20 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-16 right-1/4 h-48 w-48 rounded-full bg-violet-500/15 blur-3xl pointer-events-none" />
      </motion.div>

      {/* Stats Grid */}
      <div className="mb-10 grid grid-cols-2 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 }}
          >
            <Link
              href={stat.href}
              className="group relative flex flex-col gap-4 overflow-hidden rounded-2xl border border-border bg-card p-5 transition-all hover:border-primary/50 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-0.5"
            >
              <div className="flex items-center justify-between">
                <div className={cn("rounded-xl p-2.5 text-white transition-transform group-hover:scale-110", stat.color)}>
                  <stat.icon className="h-5 w-5" />
                </div>
                <ArrowUpRight className="h-4 w-4 text-muted-foreground transition-colors group-hover:text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold tracking-tight sm:text-3xl">{stat.value}</p>
                <p className="text-xs text-muted-foreground">{stat.name}</p>
              </div>
              <p className="text-xs font-medium text-emerald-500">{stat.trend}</p>
            </Link>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.35 }}
        className="mb-10"
      >
        <h2 className="mb-4 text-lg font-semibold">Acesso Rápido</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              href={action.href}
              className={cn(
                "flex items-center gap-3 rounded-xl border border-transparent px-4 py-3 text-sm font-medium transition-all hover:scale-[1.02] active:scale-[0.98]",
                action.color
              )}
            >
              <action.icon className="h-4 w-4 shrink-0" />
              {action.name}
            </Link>
          ))}
        </div>
      </motion.div>

      {/* Content Grid: Alerts + Recent */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Heatmap preview */}
        <div className="lg:col-span-2">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="rounded-2xl border border-border bg-card p-6"
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-primary" />
                Desempenho — 6º Ano A
              </h2>
              <Link href="/relatorios" className="text-xs text-primary hover:underline flex items-center gap-1">
                Ver Heatmap completo <ArrowUpRight className="h-3 w-3" />
              </Link>
            </div>

            {/* Mini Heatmap Preview */}
            <div className="overflow-x-auto">
              <div className="flex gap-1 min-w-max">
                {["EF06MA01", "EF06MA03", "EF06MA14", "EF06LP01", "EF06CI01"].map((skill) => (
                  <div key={skill} className="flex flex-col items-center gap-1">
                    <span className="text-[10px] font-mono text-muted-foreground writing-mode-vertical mb-1">{skill}</span>
                    {[4, 2, 3, 1, 4, 3, 2, 4, 1, 3].map((level, i) => (
                      <div
                        key={i}
                        className={cn("h-6 w-6 rounded text-[10px] font-bold flex items-center justify-center text-white",
                          level === 4 ? "bg-emerald-500" : level === 3 ? "bg-blue-500" : level === 2 ? "bg-amber-400" : "bg-red-500"
                        )}
                      >
                        {level}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </div>

        {/* Alerts column */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45 }}
          className="rounded-2xl border border-border bg-card p-6 space-y-4"
        >
          <h2 className="font-semibold flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            Alunos em Alerta
          </h2>
          {[
            { name: "João Pedro A.", class_name: "6º Ano A", avg: 1.2 },
            { name: "Gabriela C.", class_name: "6º Ano A", avg: 1.4 },
            { name: "Carlos E. S.", class_name: "6º Ano B", avg: 1.8 },
          ].map((student, i) => (
            <div key={i} className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 dark:border-red-900/50 dark:bg-red-950/20 p-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/50 text-xs font-bold text-red-600 dark:text-red-400 shrink-0">
                {student.name.split(" ").map((n) => n[0]).slice(0, 2).join("")}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-red-700 dark:text-red-400 truncate">{student.name}</p>
                <p className="text-xs text-red-500/70">{student.class_name} · Média {student.avg.toFixed(1)}</p>
              </div>
            </div>
          ))}
          <Link href="/relatorios" className="block text-center text-xs text-primary hover:underline pt-2">
            Ver todos os alertas →
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
