import { useQuery, type UseQueryOptions } from "@tanstack/react-query";
import { createClient } from "@/lib/supabase/client";
import { UsersService } from "@/lib/api/generated";
import { getApiClient } from "@/lib/api/client";
import type { UserPublic } from "@/lib/api/generated/types.gen";

/**
 * Authentication Hooks
 *
 * Custom hooks for authentication and user management using TanStack Query.
 * Works with the generated API client that auto-injects Supabase tokens.
 */

/**
 * useAuth - Get current Supabase auth session
 *
 * Returns the current authenticated user's session from Supabase.
 *
 * Usage:
 *   const { data: session, isLoading } = useAuth()
 */
export function useAuth() {
  const supabase = createClient();

  return useQuery({
    queryKey: ["auth", "session"],
    queryFn: async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      return session;
    },
    staleTime: 1000 * 60 * 5, // Sessions are fresh for 5 minutes
  });
}

/**
 * useUser - Get current user data from backend API
 *
 * Fetches user profile data from the backend API using the current session's auth token.
 * The API client automatically injects the Supabase auth token.
 *
 * Usage:
 *   const { data: user, isLoading } = useUser()
 */
export function useUser(
  options?: Omit<UseQueryOptions<UserPublic>, "queryKey" | "queryFn">
) {
  return useQuery({
    queryKey: ["users", "me"],
    queryFn: async () => {
      const client = await getApiClient();
      const result = await UsersService.readUserMe({ client });
      // The API client returns { data, error, request, response }
      // Extract just the data
      if (!result.data) {
        throw new Error("Failed to fetch user data");
      }
      return result.data;
    },
    staleTime: 1000 * 60 * 5, // User data is fresh for 5 minutes
    ...options,
  });
}

/**
 * useAuthStatus - Combined auth session and user data
 *
 * Returns both the Supabase session and the user profile data.
 *
 * Usage:
 *   const { session, user, isLoading } = useAuthStatus()
 */
export function useAuthStatus() {
  const { data: session, isLoading: sessionLoading } = useAuth();
  const { data: user, isLoading: userLoading } = useUser({
    enabled: !!session, // Only fetch user if session exists
  });

  return {
    session,
    user,
    isLoading: sessionLoading || userLoading,
    isAuthenticated: !!session && !!user,
  };
}
