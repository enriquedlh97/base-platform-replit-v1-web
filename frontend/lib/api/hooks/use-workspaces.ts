import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApiClient, WorkspacesService } from "@/lib/api/client";
import type {
  WorkspaceCreate,
  WorkspaceUpdate,
} from "@/lib/api/generated/types.gen";
import { env } from "@/lib/env";

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

/**
 * Upload workspace profile image
 */
export function useUploadWorkspaceProfileImage(workspaceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => {
      // Create FormData
      const formData = new FormData();
      formData.append("profile_image", file);

      // Get API base URL
      const baseUrl = env.NEXT_PUBLIC_API_URL.replace(/\/$/, "");
      const apiBase = baseUrl.endsWith("/api/v1")
        ? baseUrl
        : `${baseUrl}/api/v1`;

      // Get auth token from Supabase session
      const { createClient } = await import("@/lib/supabase/client");
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.access_token) {
        throw new Error("Not authenticated");
      }

      const response = await fetch(
        `${apiBase}/workspaces/${workspaceId}/profile-image`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
          body: formData,
        }
      );

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Upload failed with ${response.status}`);
      }

      return await response.json();
    },
    onSuccess: () => {
      // Invalidate workspace to refetch
      queryClient.invalidateQueries({ queryKey: ["workspace"] });
    },
  });
}
