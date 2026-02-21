"use client";

import Link from "next/link";
import { useState } from "react";
import { Menu, X, GradurationCap, LogOut, LayoutDashboard, Database, BrainCircuit } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Banco de Dados", href: "/database", icon: Database },
    { name: "IA Pedagógica", href: "/ai", icon: BrainCircuit },
];

export function Navbar() {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/10 bg-background/60 backdrop-blur-xl">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="flex h-16 items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/20">
                            <span className="text-xl font-bold text-white">S</span>
                        </div>
                        <span className="text-xl font-bold tracking-tight">SGA-H</span>
                    </div>

                    {/* Desktop Menu */}
                    <div className="hidden md:block">
                        <div className="flex items-center space-x-4">
                            {navItems.map((item) => (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-secondary hover:text-primary"
                                >
                                    <item.icon className="h-4 w-4" />
                                    {item.name}
                                </Link>
                            ))}
                            <button className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all hover:scale-105 active:scale-95">
                                <LogOut className="h-4 w-4" />
                                Sair
                            </button>
                        </div>
                    </div>

                    {/* Mobile Menu Button */}
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
            <div className={cn("md:hidden bg-background/95 backdrop-blur-md overflow-hidden transition-all duration-300", isOpen ? "max-h-64 border-b border-border" : "max-h-0")}>
                <div className="space-y-1 px-2 pb-3 pt-2">
                    {navItems.map((item) => (
                        <Link
                            key={item.name}
                            href={item.href}
                            className="flex items-center gap-3 rounded-md px-3 py-2 text-base font-medium hover:bg-secondary hover:text-primary"
                            onClick={() => setIsOpen(false)}
                        >
                            <item.icon className="h-5 w-5" />
                            {item.name}
                        </Link>
                    ))}
                    <button className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-base font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20">
                        <LogOut className="h-5 w-5" />
                        Sair
                    </button>
                </div>
            </div>
        </nav>
    );
}
