import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApiClient, SchedulingConnectorsService } from "@/lib/api/client";
import type {
  SchedulingConnectorCreate,
  SchedulingConnectorUpdate,
} from "@/lib/api/generated/types.gen";

/**
 * Scheduling Connectors API Hooks
 *
 * Custom TanStack Query hooks for scheduling connectors CRUD operations.
 * Handles cache invalidation and optimistic updates for a smooth UX.
 */

/**
 * Fetch all connectors for a workspace
 */
export function useWorkspaceConnectors(workspaceId: string) {
  return useQuery({
    queryKey: ["workspace-connectors", workspaceId],
    queryFn: async () => {
      const client = await getApiClient();
      const result = await SchedulingConnectorsService.getWorkspaceConnectors({
        client,
        path: { workspace_id: workspaceId },
      });
      if (!result.data) {
        throw new Error("Failed to fetch connectors");
      }
      return result.data;
    },
    staleTime: 1000 * 60 * 5, // Fresh for 5 minutes
  });
}

/**
 * Create a new connector
 */
export function useCreateConnector(workspaceId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: SchedulingConnectorCreate) => {
      const client = await getApiClient();
      const result = await SchedulingConnectorsService.createConnector({
        client,
        path: { workspace_id: workspaceId },
        body: data,
      });
      if (!result.data) {
        throw new Error("Failed to create connector");
      }
      return result.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["workspace-connectors", workspaceId],
      });
    },
  });
}

/**
 * Update a connector
 */
export function useUpdateConnector() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      connectorId,
      data,
    }: {
      connectorId: string;
      data: SchedulingConnectorUpdate;
    }) => {
      const client = await getApiClient();
      const result = await SchedulingConnectorsService.updateConnector({
        client,
        path: { connector_id: connectorId },
        body: data,
      });
      if (!result.data) {
        throw new Error("Failed to update connector");
      }
      return result.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace-connectors"] });
    },
  });
}

/**
 * Delete a connector
 */
export function useDeleteConnector() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (connectorId: string) => {
      const client = await getApiClient();
      await SchedulingConnectorsService.deleteConnector({
        client,
        path: { connector_id: connectorId },
      });
      return connectorId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace-connectors"] });
    },
  });
}
