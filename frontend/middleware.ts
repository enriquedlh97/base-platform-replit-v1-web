import { type NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/**
 * Next.js Middleware for Route Protection
 *
 * Intercepts requests and:
 * - Checks authentication status from cookies
 * - Redirects unauthenticated users from protected routes to /login
 * - Redirects authenticated users from auth pages to /dashboard
 * - Allows public routes like /, /login, /signup, and /c/* (public chat)
 *
 * Protected routes: /dashboard/*
 * Public routes: /, /login, /signup, /c/*
 */

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Public routes that don't require authentication
  const publicRoutes = ["/", "/login", "/signup"];
  const isPublicRoute = publicRoutes.some((route) => pathname === route);
  const isPublicChat = pathname.startsWith("/c/");

  // Allow public routes and public chat
  if (isPublicRoute || isPublicChat) {
    // Check if user is authenticated and redirect them away from auth pages
    const supabase = await createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    // If authenticated and on login/signup, redirect to dashboard
    if (session && (pathname === "/login" || pathname === "/signup")) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }

    return NextResponse.next();
  }

  // Protected routes - check authentication
  if (pathname.startsWith("/dashboard") || pathname.startsWith("/workspace")) {
    const supabase = await createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    // Redirect to login if not authenticated
    if (!session) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }

    return NextResponse.next();
  }

  // Allow all other routes
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api routes
     * - _next (Next.js internals)
     * - _static (static files)
     * - favicon.ico, sitemap, robots.txt, etc.
     */
    "/((?!api|_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)",
  ],
};
