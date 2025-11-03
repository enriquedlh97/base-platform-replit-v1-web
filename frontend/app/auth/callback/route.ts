import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";

/**
 * OAuth Callback Handler
 *
 * Handles OAuth callbacks from social authentication providers (Google, Apple).
 * Exchanges the authorization code for a session and redirects to the specified destination.
 */
export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const redirectTo =
    requestUrl.searchParams.get("redirect") || "/knowledge-base";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (error) {
      // Redirect to login with error
      const loginUrl = new URL("/login", requestUrl.origin);
      loginUrl.searchParams.set("error", "authentication_failed");
      return NextResponse.redirect(loginUrl);
    }
  }

  // Redirect to the original destination or dashboard
  return NextResponse.redirect(new URL(redirectTo, requestUrl.origin));
}
