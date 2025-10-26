"use client";

import {
  createClient as createApiClient,
  type Client,
} from "@/lib/api/generated/client";
import type { Config } from "@/lib/api/generated/client";

/**
 * API Client with Supabase Auth Injection
 *
 * This client automatically injects Supabase auth tokens into all API requests.
 * Use this in Client Components.
 *
 * Usage:
 *   import { apiClient } from "@/lib/api/client"
 *   import { UsersService } from "@/lib/api/generated"
 *   const client = await apiClient
 *   const user = await UsersService.readUserMe({ client })
 */

let apiClientInstance: Client | null = null;

/**
 * Get or create the API client instance with automatic auth token injection
 * This ensures we only create one client instance
 */
export const getApiClient = async (): Promise<Client> => {
  if (apiClientInstance) return apiClientInstance;

  // Import Supabase client
  const { createClient } = await import("@/lib/supabase/client");
  const supabase = createClient();

  // Create API client with auth token injection via interceptors
  const config: Config = {
    baseUrl: process.env.NEXT_PUBLIC_API_URL,
    headers: new Headers(),
  };

  const client = createApiClient(config);

  // Add request interceptor to inject auth token
  client.interceptors.request.use(async (request: Request) => {
    // Get current session
    const {
      data: { session },
    } = await supabase.auth.getSession();

    // Add auth token if available
    if (session?.access_token) {
      request.headers.set("Authorization", `Bearer ${session.access_token}`);
    }

    return request;
  });

  apiClientInstance = client;
  return client;
};

/**
 * Default API client for convenience
 * Uses getApiClient() under the hood
 */
export const apiClient = getApiClient();

/**
 * Re-export services for convenience
 * Usage: import { UsersService } from "@/lib/api/client"
 */
export {
  UsersService,
  WorkspacesService,
  LoginService,
  ConversationsService,
  SchedulingConnectorsService,
} from "@/lib/api/generated";
