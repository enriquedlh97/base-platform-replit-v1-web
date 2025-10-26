"use client";

import { createBrowserClient } from "@supabase/ssr";
import { env } from "@/lib/env";

/**
 * Supabase Client for Browser/Client Components
 *
 * This creates a Supabase client that works in Client Components and hooks.
 * For Server Components, use createClient() from '@/lib/supabase/server'
 *
 * Uses @supabase/ssr for proper cookie handling that's compatible with the server client.
 *
 * Usage:
 *   import { createClient } from "@/lib/supabase/client"
 *   const supabase = createClient()
 *   const { data } = await supabase.auth.getSession()
 */

export const createClient = () => {
  return createBrowserClient(
    env.NEXT_PUBLIC_SUPABASE_URL,
    env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  );
};
