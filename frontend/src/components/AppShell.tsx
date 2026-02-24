"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, GraduationCap, LogOut, Bell, Search } from "lucide-react";
import { Sidebar } from "@/components/Sidebar";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/useAuth";

interface AppShellProps {
    children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const pathname = usePathname();
    const { user, logout } = useAuth();

    // Don't render the shell on login page
    const isLoginPage = pathname === "/login";

    if (isLoginPage) {
        return <>{children}</>;
    }

    return (
        <div className="min-h-screen">
            {/* Top Navigation Bar */}
            <header className="fixed top-0 left-0 right-0 z-50 h-16 border-b border-border bg-background/80 backdrop-blur-xl">
                <div className="flex h-full items-center gap-4 px-4">

                    {/* Sidebar toggle (mobile + desktop ) */}
                    <button
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground lg:hidden"
                    >
                        {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                    </button>

                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2.5 font-bold">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary shadow-lg shadow-primary/30">
                            <GraduationCap className="h-4 w-4 text-white" />
                        </div>
                        <span className="hidden text-lg tracking-tight sm:block">SGA-H</span>
                    </Link>

                    {/* Search Bar */}
                    <div className="ml-4 flex flex-1 items-center gap-2 rounded-xl border border-border bg-secondary px-3 py-2 max-w-md">
                        <Search className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        <input
                            type="text"
                            placeholder="Buscar alunos, habilidades..."
                            className="flex-1 bg-transparent text-sm focus:outline-none placeholder:text-muted-foreground"
                        />
                    </div>

                    {/* Right side actions */}
                    <div className="ml-auto flex items-center gap-2">
                        <button className="relative flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground">
                            <Bell className="h-5 w-5" />
                            <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-primary" />
                        </button>

                        {/* User Avatar */}
                        <div className="flex items-center gap-2 rounded-xl border border-border bg-secondary px-3 py-1.5">
                            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-bold text-white uppercase">
                                {user ? (user.full_name || user.username || "?")[0] : "?"}
                            </div>
                            <span className="hidden text-sm font-medium sm:block capitalize">
                                {user ? (user.role === "coordinator" ? "Coordenador" : user.role === "admin" ? "Admin" : "Professor") : "Carregando..."}
                            </span>
                        </div>

                        <button onClick={logout} className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-secondary hover:text-red-500" title="Sair do sistema">
                            <LogOut className="h-4 w-4" />
                        </button>
                    </div>
                </div>
            </header>

            {/* Layout with Sidebar */}
            <div className="flex pt-16 min-h-screen">
                <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

                {/* Main Content */}
                <main className={cn(
                    "flex-1 min-w-0 transition-all duration-300",
                    "lg:ml-64"
                )}>
                    {/* Subtle background grid */}
                    <div className="fixed inset-0 -z-10 bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] dark:bg-[radial-gradient(#ffffff08_1px,transparent_1px)] [background-size:20px_20px] pointer-events-none" />
                    {children}
                </main>
            </div>
        </div>
    );
}
