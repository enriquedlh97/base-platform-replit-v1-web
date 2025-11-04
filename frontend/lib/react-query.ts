import { QueryClient } from "@tanstack/react-query";

/**
 * TanStack Query Client Configuration
 *
 * This configures the default behavior for all TanStack Query hooks.
 *
 * Defaults:
 * - staleTime: 5 minutes - how long data is considered fresh
 * - gcTime: 10 minutes - how long unused data stays in cache
 * - retry: 3 times with exponential backoff
 * - refetchOnWindowFocus: true - refetch when window regains focus
 *
 * Usage:
 *   import { queryClient } from "@/lib/react-query"
 *   const { data } = useQuery({ queryKey: ["users"], queryFn: fetchUsers })
 */

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Data is fresh for 5 minutes
      staleTime: 1000 * 60 * 5,
      // Unused data stays in cache for 10 minutes
      gcTime: 1000 * 60 * 10,
      // Retry failed requests 3 times with exponential backoff
      retry: 3,
      // Refetch when window regains focus
      refetchOnWindowFocus: true,
      // Don't refetch on mount if data is fresh
      refetchOnMount: false,
    },
    mutations: {
      // Retry mutations once if they fail
      retry: 1,
    },
  },
});
