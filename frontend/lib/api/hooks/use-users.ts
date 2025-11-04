import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApiClient, UsersService } from "@/lib/api/client";
import type { UserUpdateMe } from "@/lib/api/generated/types.gen";

/**
 * Users API Hooks
 *
 * Custom TanStack Query hooks for user CRUD operations.
 * Handles cache invalidation and optimistic updates for a smooth UX.
 */

/**
 * Fetch current user
 */
export function useUser() {
  return useQuery({
    queryKey: ["users", "me"],
    queryFn: async () => {
      const client = await getApiClient();
      const result = await UsersService.readUserMe({ client });
      if (!result.data) {
        throw new Error("Failed to fetch user");
      }
      return result.data;
    },
    staleTime: 1000 * 60 * 5, // Fresh for 5 minutes
  });
}

/**
 * Update current user
 */
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UserUpdateMe) => {
      const client = await getApiClient();
      const result = await UsersService.updateUserMe({
        client,
        body: data,
      });
      if (!result.data) {
        throw new Error("Failed to update user");
      }
      return result.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      queryClient.invalidateQueries({ queryKey: ["workspace"] });
    },
  });
}
