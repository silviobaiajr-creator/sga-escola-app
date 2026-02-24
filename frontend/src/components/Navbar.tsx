"use client";

import { useAuth } from "@/lib/useAuth";
import { GraduationCap, LogOut } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

export function Navbar() {
    const { user, logout } = useAuth();

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-background/60 backdrop-blur-xl">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="flex h-16 items-center justify-between">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2 transition-transform hover:scale-105">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-violet-600 shadow-lg shadow-primary/20">
                            <GraduationCap className="h-5 w-5 text-white" />
                        </div>
                        <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-primary to-violet-400 bg-clip-text text-transparent">SGA-H</span>
                    </Link>

                    {/* Right side: User Info + Logout */}
                    {user && (
                        <div className="flex items-center gap-2 sm:gap-4">
                            {/* User Badge */}
                            <div className="flex items-center gap-2 rounded-xl border border-border bg-secondary/50 p-1 pr-3 sm:py-1.5 backdrop-blur-sm">
                                <div className="flex h-7 w-7 sm:h-6 sm:w-6 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs sm:text-[10px] font-bold text-primary">
                                    {(user.full_name || user.username || "?")[0].toUpperCase()}
                                </div>
                                <div className="flex flex-col sm:flex-row sm:items-center sm:gap-2">
                                    <span className="text-xs sm:text-sm font-medium line-clamp-1 max-w-[100px] sm:max-w-[200px] leading-none">
                                        {user.full_name || user.username}
                                    </span>
                                    <span className="hidden sm:inline-block rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary capitalize">
                                        {user.role === "coordinator" ? "Coordenador" : user.role === "admin" ? "Admin" : "Professor"}
                                    </span>
                                </div>
                            </div>

                            {/* Logout Button */}
                            <button
                                onClick={logout}
                                className="flex items-center justify-center gap-2 rounded-xl border border-red-500/20 bg-red-500/5 p-2 sm:px-3 sm:py-1.5 text-sm font-medium text-red-500 transition-all hover:bg-red-500/10 hover:scale-105 active:scale-95 shadow-sm"
                                title="Sair do sistema"
                            >
                                <LogOut className="h-4 w-4 shrink-0 sm:h-4 sm:w-4" />
                                <span className="hidden sm:inline">Sair</span>
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </nav>
    );
}

