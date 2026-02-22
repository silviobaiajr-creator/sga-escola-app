"use client";

import Link from "next/link";
import { useState } from "react";
import { Menu, X, GraduationCap, LogOut, LayoutDashboard } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/useAuth";

const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
];

export function Navbar() {
    const [isOpen, setIsOpen] = useState(false);
    const { user, logout } = useAuth();

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-background/60 backdrop-blur-xl">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="flex h-16 items-center justify-between">
                    {/* Logo */}
                    <div className="flex items-center gap-2">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/20">
                            <GraduationCap className="h-5 w-5 text-white" />
                        </div>
                        <span className="text-xl font-bold tracking-tight">SGA-H</span>
                    </div>

                    {/* Desktop: usuário + logout */}
                    <div className="hidden md:flex items-center gap-3">
                        {user && (
                            <div className="flex items-center gap-2 rounded-xl border border-border bg-secondary/50 px-3 py-1.5">
                                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20 text-[10px] font-bold text-primary">
                                    {(user.full_name || user.username || "?")[0].toUpperCase()}
                                </div>
                                <span className="text-sm font-medium">{user.full_name || user.username}</span>
                                <span className="rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary capitalize">
                                    {user.role === "coordinator" ? "Coordenador" : user.role === "admin" ? "Admin" : "Professor"}
                                </span>
                            </div>
                        )}
                        <button
                            onClick={logout}
                            className="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/5 px-3 py-1.5 text-sm font-medium text-red-400 transition-all hover:bg-red-500/10 hover:scale-105 active:scale-95"
                        >
                            <LogOut className="h-4 w-4" />
                            Sair
                        </button>
                    </div>

                    {/* Mobile: hamburger */}
                    <div className="md:hidden">
                        <button
                            onClick={() => setIsOpen(!isOpen)}
                            className="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:bg-secondary hover:text-primary focus:outline-none"
                        >
                            {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Menu */}
            <div className={cn(
                "md:hidden bg-background/95 backdrop-blur-md overflow-hidden transition-all duration-300",
                isOpen ? "max-h-64 border-b border-border" : "max-h-0"
            )}>
                <div className="space-y-1 px-2 pb-3 pt-2">
                    {user && (
                        <div className="flex items-center gap-2 rounded-xl border border-border bg-secondary/50 px-3 py-2 mb-2">
                            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20 text-[10px] font-bold text-primary">
                                {(user.full_name || user.username || "?")[0].toUpperCase()}
                            </div>
                            <span className="text-sm font-medium">{user.full_name || user.username}</span>
                        </div>
                    )}
                    <button
                        onClick={() => { logout(); setIsOpen(false); }}
                        className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-base font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20"
                    >
                        <LogOut className="h-5 w-5" />
                        Sair
                    </button>
                </div>
            </div>
        </nav>
    );
}
