"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  ArrowUpRight, Users, GraduationCap, ClipboardCheck, Sparkles,
  BarChart3, AlertTriangle, Play
} from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { getDashboardData } from "@/lib/api";

const quickActions = [
  { name: "Nova Avaliação", href: "/avaliacao", icon: ClipboardCheck, color: "bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-950/30 dark:text-emerald-400 dark:hover:bg-emerald-950/50" },
  { name: "Gerar com IA", href: "/ia", icon: Sparkles, color: "bg-violet-50 text-violet-700 hover:bg-violet-100 dark:bg-violet-950/30 dark:text-violet-400 dark:hover:bg-violet-950/50" },
  { name: "Ver Relatórios", href: "/relatorios", icon: BarChart3, color: "bg-blue-50 text-blue-700 hover:bg-blue-100 dark:bg-blue-950/30 dark:text-blue-400 dark:hover:bg-blue-950/50" },
  { name: "Lista de Alunos", href: "/alunos", icon: Users, color: "bg-orange-50 text-orange-700 hover:bg-orange-100 dark:bg-orange-950/30 dark:text-orange-400 dark:hover:bg-orange-950/50" },
];

export default function Home() {
  const [dashboard, setDashboard] = useState<any>(null);

  useEffect(() => {
    getDashboardData().then(r => setDashboard(r.data)).catch(() => { });
  }, []);

  const summary = dashboard?.summary || { total_students: "--", total_assessments: "--", approved_objectives: "--", pending_approvals: "--" };
  const skillAlerts = dashboard?.skill_alerts || [];
  const classAvgs = dashboard?.class_averages || [];

  const topClassAvgs = [...classAvgs].sort((a, b) => b.average_level - a.average_level).slice(0, 3);

  const stats = [
    { name: "Total de Alunos", value: summary.total_students, icon: Users, color: "bg-blue-500", trend: "Consulte a listagem", href: "/alunos" },
    { name: "Objetivos Aprovados", value: summary.approved_objectives, icon: GraduationCap, color: "bg-purple-500", trend: "Na Biblioteca BNCC", href: "/planejamento/objetivos" },
    { name: "Avaliações", value: summary.total_assessments, icon: ClipboardCheck, color: "bg-emerald-500", trend: "Registros de notas", href: "/avaliacao" },
    { name: "IA Pendentes", value: summary.pending_approvals, icon: Sparkles, color: "bg-amber-500", trend: "Aprovação pendente", href: "/planejamento/objetivos" },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Hero Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative mb-10 overflow-hidden rounded-3xl bg-gradient-to-br from-neutral-900 to-neutral-800 px-8 py-10 text-white shadow-xl"
      >
        <div className="relative z-10 max-w-2xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs backdrop-blur">
            <Sparkles className="h-3 w-3 text-amber-400" />
            <span>Powered by Anthropic & Google AI</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
            Bem-vindo ao <span className="bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">SGA-H Escola</span>
          </h1>
          <p className="mt-4 text-base text-neutral-400 sm:text-lg">
            Plataforma inovadora de gestão por habilidades (BNCC). Monitore, gere rubricas automatizadas e acompanhe a evolução dos alunos de forma ágil e precisa.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <Link
              href="/avaliacao"
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-bold text-white shadow-lg shadow-primary/30 transition-all hover:scale-105 active:scale-95"
            >
              <ClipboardCheck className="h-4 w-4" />
              Realizar Avaliação
            </Link>
            <Link
              href="/relatorios"
              className="inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-6 py-3 text-sm font-semibold backdrop-blur-sm transition-all hover:bg-white/10"
            >
              <BarChart3 className="h-4 w-4" />
              Painel Completo do Coordenador
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
              <p className="text-[10px] font-medium text-emerald-500 uppercase tracking-widest">{stat.trend}</p>
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
        <h2 className="mb-4 text-lg font-semibold border-l-4 border-primary pl-3">Acesso Rápido</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              href={action.href}
              className={cn(
                "flex items-center gap-3 rounded-xl border border-transparent px-4 py-4 text-sm font-semibold transition-all hover:scale-[1.02] active:scale-[0.98] shadow-sm",
                action.color
              )}
            >
              <action.icon className="h-5 w-5 shrink-0" />
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
            className="rounded-2xl border border-border bg-card p-6 h-full flex flex-col"
          >
            <div className="mb-6 flex items-center justify-between">
              <h2 className="font-semibold flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary" />
                Top Turmas em Desempenho
              </h2>
              <Link href="/relatorios" className="text-xs text-primary hover:underline flex items-center gap-1">
                Ver tabelas completas <ArrowUpRight className="h-3 w-3" />
              </Link>
            </div>

            {topClassAvgs.length > 0 ? (
              <div className="space-y-4 flex-1">
                {topClassAvgs.map((cls, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-xl border border-border bg-card/60">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center font-bold text-xs border border-emerald-500/20">
                        {i + 1}º
                      </div>
                      <p className="font-semibold">{cls.class_name}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-xs text-muted-foreground">{cls.total_assessments} aval.</span>
                      <div className="px-3 py-1 rounded bg-secondary/80 border border-border font-bold text-primary">N{cls.average_level.toFixed(1)}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center py-6 text-muted-foreground">
                <BarChart3 className="mb-2 h-10 w-10 opacity-20" />
                <p className="text-sm">Os dados de proficiência aparecerão aqui após as primeiras avaliações.</p>
              </div>
            )}
          </motion.div>
        </div>

        {/* Alerts column */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45 }}
          className="rounded-2xl border border-border bg-card p-6 space-y-4 flex flex-col"
        >
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Alertas CHT
            </h2>
          </div>

          {skillAlerts.length > 0 ? (
            <div className="space-y-3 flex-1 overflow-y-auto max-h-[250px] pr-2">
              {skillAlerts.slice(0, 4).map((alert: any, i: number) => (
                <div key={i} className="p-3 rounded-lg border border-amber-500/20 bg-amber-500/5">
                  <p className="text-xs font-bold font-mono text-amber-600 dark:text-amber-400">{alert.bncc_code}</p>
                  <div className="flex justify-between items-end mt-2">
                    <span className="text-[10px] text-muted-foreground">{alert.at_risk_count} alunos ({alert.at_risk_pct}%) N1/N2</span>
                    <span className="text-xs font-bold">Média {alert.average_level.toFixed(1)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center py-4 text-muted-foreground">
              <p className="text-sm text-center">Nenhuma habilidade em estado de alerta crítico por enquanto.</p>
            </div>
          )}

          <Link href="/relatorios" className="block text-center text-xs text-primary font-bold hover:underline pt-2 border-t border-border/50">
            Ver análise completa →
          </Link>
        </motion.div>
      </div>
    </div>
  );
}

