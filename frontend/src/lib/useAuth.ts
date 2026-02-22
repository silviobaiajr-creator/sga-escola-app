/**
 * useAuth — Hook centralizado de autenticação
 * Lê o token e o usuário do localStorage/cookie.
 * Expõe: user, token, isLoading, login(), logout()
 */
"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "./api";

export interface SgaUser {
    id: string;
    username: string;
    full_name?: string;
    email?: string;
    role: "admin" | "coordinator" | "teacher";
    is_active: boolean;
}

interface AuthState {
    user: SgaUser | null;
    token: string | null;
    isLoading: boolean;
}

// ── Helpers de storage ──────────────────────────────────────
function saveAuth(token: string, user: SgaUser) {
    localStorage.setItem("sga_token", token);
    localStorage.setItem("sga_user", JSON.stringify(user));
    // Salvar no cookie para que o middleware Edge consiga ler
    document.cookie = `sga_token=${token}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Strict`;
}

function clearAuth() {
    localStorage.removeItem("sga_token");
    localStorage.removeItem("sga_user");
    document.cookie = "sga_token=; path=/; max-age=0";
}

function readAuth(): { token: string | null; user: SgaUser | null } {
    if (typeof window === "undefined") return { token: null, user: null };
    const token = localStorage.getItem("sga_token");
    const raw = localStorage.getItem("sga_user");
    try { return { token, user: raw ? JSON.parse(raw) : null }; }
    catch { return { token, user: null }; }
}

// ── Hook ────────────────────────────────────────────────────
export function useAuth() {
    const router = useRouter();
    const [state, setState] = useState<AuthState>({
        user: null, token: null, isLoading: true,
    });

    // Inicializar a partir do storage
    useEffect(() => {
        const { token, user } = readAuth();
        setState({ token, user, isLoading: false });
    }, []);

    // login() — chama a API e salva o resultado
    const login = useCallback(async (username: string, password: string): Promise<void> => {
        setState(s => ({ ...s, isLoading: true }));
        try {
            const res = await api.post<{ access_token: string; user: SgaUser }>(
                "/api/auth/login", { username, password }
            );
            const { access_token, user } = res.data;
            saveAuth(access_token, user);
            setState({ token: access_token, user, isLoading: false });

            // Redirecionar para a URL original ou raiz
            const params = new URLSearchParams(window.location.search);
            router.push(params.get("next") || "/");
        } catch (err: any) {
            setState(s => ({ ...s, isLoading: false }));
            throw err;          // re-lança para o componente tratar
        }
    }, [router]);

    // logout()
    const logout = useCallback(() => {
        clearAuth();
        setState({ token: null, user: null, isLoading: false });
        router.push("/login");
    }, [router]);

    return { ...state, login, logout };
}

// ── Helper standalone para componentes server-like ou fora de hook ──
export function getStoredToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("sga_token");
}
