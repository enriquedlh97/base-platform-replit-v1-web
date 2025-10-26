"use server";

import { createClient as createSupabaseClient } from "@supabase/supabase-js";
import { cookies } from "next/headers";
import { env } from "@/lib/env";

/**
 * Supabase Client for Server Components
 *
 * This creates a Supabase client that works in Server Components and Route Handlers.
 * It reads the auth cookie from the request to maintain the user's session.
 *
 * Usage in Server Components:
 *   import { createClient } from "@/lib/supabase/server"
 *   const supabase = createClient()
 *   const { data } = await supabase.auth.getSession()
 *
 * Usage in Route Handlers:
 *   import { createClient } from "@/lib/supabase/server"
 *   export async function GET() {
 *     const supabase = createClient()
 *     const { data } = await supabase.auth.getSession()
 *     return Response.json(data)
 *   }
 */

export const createClient = async () => {
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  const refreshToken = cookieStore.get("sb-refresh-token")?.value;

  const supabase = createSupabaseClient(
    env.NEXT_PUBLIC_SUPABASE_URL,
    env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    {
      auth: {
        // Use cookies for auth persistence
        storage: {
          getItem: (key: string) => {
            return cookieStore.get(key)?.value ?? null;
          },
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          setItem: (_key, _value) => {
            // Server components can't set cookies, this is handled by middleware
            return;
          },
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          removeItem: (_key) => {
            // Server components can't remove cookies, this is handled by middleware
            return;
          },
        },
        // Provide tokens from cookies if available
        ...(accessToken && refreshToken
          ? { access_token: accessToken, refresh_token: refreshToken }
          : {}),
      },
    }
  );

  return supabase;
};
