"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
    glass?: boolean;
}

export function Card({ children, className, glass, ...props }: CardProps) {
    return (
        <div
            className={cn(
                "rounded-2xl border border-border bg-card p-6",
                glass && "glass-card",
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
    return <div className={cn("mb-4", className)}>{children}</div>;
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
    return <h3 className={cn("text-lg font-semibold", className)}>{children}</h3>;
}

export function CardContent({ children, className }: { children: React.ReactNode; className?: string }) {
    return <div className={cn("", className)}>{children}</div>;
}

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    variant?: "default" | "success" | "warning" | "error" | "info";
}

export function Badge({ children, variant = "default", className, ...props }: BadgeProps) {
    const variantClasses = {
        default: "bg-secondary text-secondary-foreground",
        success: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400",
        warning: "bg-amber-100 text-amber-700 dark:bg-amber-950/30 dark:text-amber-400",
        error: "bg-red-100 text-red-700 dark:bg-red-950/30 dark:text-red-400",
        info: "bg-blue-100 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400",
    };

    return (
        <span
            className={cn(
                "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                variantClasses[variant],
                className
            )}
            {...props}
        >
            {children}
        </span>
    );
}

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "default" | "outline" | "ghost" | "danger";
    size?: "sm" | "md" | "lg";
    loading?: boolean;
}

export function Button({
    children, variant = "default", size = "md", loading, className, disabled, ...props
}: ButtonProps) {
    const variantClasses = {
        default: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg shadow-primary/20",
        outline: "border border-border bg-transparent hover:bg-secondary",
        ghost: "bg-transparent hover:bg-secondary",
        danger: "bg-red-500 text-white hover:bg-red-600 shadow-lg shadow-red-500/20",
    };

    const sizeClasses = {
        sm: "px-3 py-1.5 text-sm",
        md: "px-4 py-2 text-sm",
        lg: "px-6 py-3 text-base",
    };

    return (
        <button
            className={cn(
                "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:pointer-events-none",
                variantClasses[variant],
                sizeClasses[size],
                loading && "opacity-80 cursor-wait",
                className
            )}
            disabled={disabled || loading}
            {...props}
        >
            {loading && (
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
            )}
            {children}
        </button>
    );
}
