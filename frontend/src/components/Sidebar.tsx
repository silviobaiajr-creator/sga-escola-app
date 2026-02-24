"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
    LayoutDashboard,
    Users,
    ClipboardCheck,
    BookOpen,
    BarChart3,
    ShieldCheck,
    ChevronRight,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/useAuth";

const menuItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    {
        name: "Planejamento",
        icon: BookOpen,
        children: [
            { name: "Biblioteca BNCC", href: "/planejamento/bncc" },
            { name: "Objetivos e Rubricas", href: "/planejamento/objetivos" },
            { name: "Consultor Pedagógico", href: "/planejamento/consultor" },
        ],
    },
    { name: "Avaliação", href: "/avaliacao", icon: ClipboardCheck },
    { name: "Alunos", href: "/alunos", icon: Users },
    { name: "Relatórios", href: "/relatorios", icon: BarChart3 },
    { name: "Administração", href: "/admin", icon: ShieldCheck },
];


interface SidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
    const pathname = usePathname();
    const [expandedItems, setExpandedItems] = React.useState<string[]>([]);
    const { user } = useAuth();

    const toggleExpanded = (name: string) => {
        setExpandedItems((prev) =>
            prev.includes(name) ? prev.filter((i) => i !== name) : [...prev, name]
        );
    };

    const sidebarItems = menuItems.filter(item => {
        if (item.name === "Administração" && user?.role !== "admin" && user?.role !== "coordinator") {
            return false;
        }
        return true;
    });

    return (
        <>
            {/* Desktop Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
                    onClick={onClose}
                />
            )}

            {/* Sidebar Element */}
            <aside className={cn(
                "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border bg-background pt-16 transition-transform duration-300 lg:translate-x-0",
                isOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                {/* Scrollable Navigation */}
                <div className="flex-1 overflow-y-auto overflow-x-hidden p-4">
                    <nav className="flex flex-col gap-2">
                        {sidebarItems.map((item) => {
                            const isActive = pathname === item.href;
                            const isExpanded = expandedItems.includes(item.name);

                            if (item.children) {
                                return (
                                    <div key={item.name}>
                                        <button
                                            onClick={() => toggleExpanded(item.name)}
                                            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors hover:bg-secondary"
                                        >
                                            {item.icon && <item.icon className="h-4 w-4 flex-shrink-0 text-muted-foreground" />}
                                            <span className="flex-1 text-left">{item.name}</span>
                                            <ChevronRight
                                                className={cn(
                                                    "h-4 w-4 text-muted-foreground transition-transform",
                                                    isExpanded && "rotate-90"
                                                )}
                                            />
                                        </button>
                                        {isExpanded && (
                                            <div className="mt-1 ml-4 flex flex-col gap-1 pl-3 border-l border-border">
                                                {item.children.map((child) => (
                                                    <Link
                                                        key={child.href}
                                                        href={child.href}
                                                        onClick={onClose}
                                                        className={cn(
                                                            "flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors",
                                                            pathname === child.href
                                                                ? "bg-primary/10 text-primary font-medium"
                                                                : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                                                        )}
                                                    >
                                                        {child.name}
                                                    </Link>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                );
                            }

                            return (
                                <Link
                                    key={item.name}
                                    href={item.href!}
                                    onClick={onClose}
                                    className={cn(
                                        "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                                        isActive
                                            ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                                            : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                                    )}
                                >
                                    {isActive && (
                                        <motion.div
                                            layoutId="sidebar-active"
                                            className="absolute inset-0 rounded-xl bg-primary"
                                            style={{ zIndex: -1 }}
                                            transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                                        />
                                    )}
                                    {item.icon && <item.icon className="h-4 w-4 flex-shrink-0" />}
                                    {item.name}
                                </Link>
                            );
                        })}
                </div>

                {/* Bottom section */}
                <div className="border-t border-border p-4">
                    <div className="rounded-xl bg-secondary p-3">
                        {user ? (
                            <div className="flex items-center gap-3">
                                <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-white text-sm font-bold">
                                    {(user.full_name || user.username || "?")[0].toUpperCase()}
                                </div>
                                <div>
                                    <p className="text-sm font-medium">{user.full_name || user.username}</p>
                                    <p className="text-xs text-muted-foreground capitalize">
                                        {user.role === "coordinator" ? "Coordenador" : user.role === "admin" ? "Admin" : "Professor"}
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <div className="flex items-center gap-3">
                                <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-white text-sm font-bold">
                                    ?
                                </div>
                                <div>
                                    <p className="text-sm font-medium">Carregando...</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </aside >
        </>
    );
}
