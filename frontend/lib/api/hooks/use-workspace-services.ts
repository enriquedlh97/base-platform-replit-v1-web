import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApiClient, WorkspaceServicesService } from "@/lib/api/client";
import type {
  WorkspaceServiceCreate,
  WorkspaceServiceUpdate,
} from "@/lib/api/generated/types.gen";

/**
 * Workspace Services API Hooks
 *
 * Custom TanStack Query hooks for workspace services CRUD operations.
 * Handles cache invalidation and optimistic updates for a smooth UX.
 */

/**
 * Fetch all services for a workspace
 */
export function useWorkspaceServices(workspaceId: string) {
  return useQuery({
    queryKey: ["workspace-services", workspaceId],
    queryFn: async () => {
      const client = await getApiClient();
      const result = await WorkspaceServicesService.getWorkspaceServices({
        client,
        path: { workspace_id: workspaceId },
      });
      if (!result.data) {
        throw new Error("Failed to fetch services");
      }
      return result.data;
    },
    staleTime: 1000 * 60 * 5, // Fresh for 5 minutes
  });
}

/**
 * Create a new service
 */
export function useCreateWorkspaceService(workspaceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: WorkspaceServiceCreate) => {
      const client = await getApiClient();
      const result = await WorkspaceServicesService.createWorkspaceService({
        client,
        path: { workspace_id: workspaceId },
        body: data,
      });
      if (!result.data) {
        throw new Error("Failed to create service");
      }
      return result.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["workspace-services", workspaceId],
      });
    },
  });
}

/**
 * Update a service
 */
export function useUpdateWorkspaceService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      serviceId,
      data,
    }: {
      serviceId: string;
      data: WorkspaceServiceUpdate;
    }) => {
      const client = await getApiClient();
      const result = await WorkspaceServicesService.updateService({
        client,
        path: { service_id: serviceId },
        body: data,
      });
      if (!result.data) {
        throw new Error("Failed to update service");
      }
      return result.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace-services"] });
    },
  });
}

/**
 * Delete a service
 */
export function useDeleteWorkspaceService() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (serviceId: string) => {
      const client = await getApiClient();
      await WorkspaceServicesService.deleteService({
        client,
        path: { service_id: serviceId },
      });
      return serviceId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace-services"] });
    },
  });
}
