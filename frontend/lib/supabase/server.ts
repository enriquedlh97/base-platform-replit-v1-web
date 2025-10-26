"use server";

import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { env } from "@/lib/env";

/**
 * Supabase Client for Server Components
 *
 * This creates a Supabase client that works in Server Components and Route Handlers.
 * It reads the auth cookie from the request to maintain the user's session.
 *
 * Uses @supabase/ssr for proper cookie handling in Next.js App Router.
 *
 * Usage in Server Components:
 *   import { createClient } from "@/lib/supabase/server"
 *   const supabase = await createClient()
 *   const { data } = await supabase.auth.getSession()
 *
 * Usage in Route Handlers:
 *   import { createClient } from "@/lib/supabase/server"
 *   export async function GET() {
 *     const supabase = await createClient()
 *     const { data } = await supabase.auth.getSession()
 *     return Response.json(data)
 *   }
 */

export const createClient = async () => {
  const cookieStore = await cookies();

  return createServerClient(
    env.NEXT_PUBLIC_SUPABASE_URL,
    env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) => {
              cookieStore.set(name, value, options);
            });
          } catch {
            // The `setAll` method was called from a Server Component.
            // This can be ignored if you have middleware refreshing user sessions.
          }
        },
      },
    }
  );
};
