import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApiClient, WorkspacesService } from "@/lib/api/client";
import type {
  WorkspaceCreate,
  WorkspaceUpdate,
} from "@/lib/api/generated/types.gen";

/**
 * Workspace API Hooks
 *
 * Custom TanStack Query hooks for workspace CRUD operations.
 * Handles cache invalidation and optimistic updates for a smooth UX.
 *
 * Note: Each user has exactly ONE workspace (backend constraint).
 */

/**
 * Fetch current user's workspace
 */
export function useWorkspace() {
  return useQuery({
    queryKey: ["workspace", "me"],
    queryFn: async () => {
      const client = await getApiClient();
      const result = await WorkspacesService.getMyWorkspace({ client });
      if (!result.data) {
        throw new Error("Failed to fetch workspace");
      }
      return result.data;
    },
    staleTime: 1000 * 60 * 5, // Fresh for 5 minutes
  });
}

/**
 * Create a new workspace
 */
export function useCreateWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: WorkspaceCreate) => {
      const client = await getApiClient();
      const result = await WorkspacesService.createWorkspace({
        client,
        body: data,
      });
      if (!result.data) {
        throw new Error("Failed to create workspace");
      }
      return result.data;
    },
    onSuccess: () => {
      // Invalidate workspace to refetch
      queryClient.invalidateQueries({ queryKey: ["workspace"] });
      // Also invalidate user data to update setup_completed flag
      queryClient.invalidateQueries({ queryKey: ["users", "me"] });
    },
  });
}

/**
 * Update the workspace
 */
export function useUpdateWorkspace(workspaceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: WorkspaceUpdate) => {
      const client = await getApiClient();
      const result = await WorkspacesService.updateWorkspace({
        client,
        path: { workspace_id: workspaceId },
        body: data,
      });
      if (!result.data) {
        throw new Error("Failed to update workspace");
      }
      return result.data;
    },
    onSuccess: () => {
      // Invalidate workspace to refetch
      queryClient.invalidateQueries({ queryKey: ["workspace"] });
    },
  });
}

/**
 * Delete the workspace
 */
export function useDeleteWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (workspaceId: string) => {
      const client = await getApiClient();
      await WorkspacesService.deleteWorkspace({
        client,
        path: { workspace_id: workspaceId },
      });
      return workspaceId;
    },
    onSuccess: () => {
      // Invalidate workspace to refetch
      queryClient.invalidateQueries({ queryKey: ["workspace"] });
    },
  });
}
