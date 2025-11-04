import { z } from "zod";

/**
 * Environment variable validation schema
 *
 * This ensures all required environment variables are present and valid at startup.
 * If validation fails, the app will throw a clear error with missing/invalid variables.
 *
 * Usage:
 *   import { env } from "@/lib/env"
 *   // Access validated environment variables
 *   const apiUrl = env.NEXT_PUBLIC_API_URL
 */

const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url().describe("Backend API base URL"),
  NEXT_PUBLIC_SUPABASE_URL: z.string().url().describe("Supabase project URL"),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z
    .string()
    .min(1)
    .describe("Supabase anonymous key"),
});

export const env = envSchema.parse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
});

/**
 * TypeScript type for environment variables
 * Inferred from the Zod schema for type safety throughout the app
 */
export type Env = z.infer<typeof envSchema>;
