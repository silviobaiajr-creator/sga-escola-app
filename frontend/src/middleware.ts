import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware de autenticação — executa em toda requisição do Next.js
 * Rotas públicas: /login
 * Todas as demais rotas requerem sga_token no cookie ou header
 */

const PUBLIC_PATHS = ["/login"];

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Deixar passar rotas públicas e assets internos do Next.js
    if (
        PUBLIC_PATHS.some((p) => pathname.startsWith(p)) ||
        pathname.startsWith("/_next") ||
        pathname.startsWith("/favicon")
    ) {
        return NextResponse.next();
    }

    // Verificar token no cookie (enviado pelo browser) ou header Authorization
    const tokenFromCookie = request.cookies.get("sga_token")?.value;
    const authHeader = request.headers.get("authorization");
    const tokenFromHeader = authHeader?.startsWith("Bearer ")
        ? authHeader.slice(7)
        : null;

    const hasToken = Boolean(tokenFromCookie || tokenFromHeader);

    if (!hasToken) {
        // Redirecionar para /login passando a URL original como ?next=
        const loginUrl = new URL("/login", request.url);
        loginUrl.searchParams.set("next", pathname);
        return NextResponse.redirect(loginUrl);
    }

    return NextResponse.next();
}

// Aplicar o middleware em todas as rotas exceto assets estáticos
export const config = {
    matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\..*).*)"],
};
