import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApiClient, CuaTasksService } from "@/lib/api/client";
import type {
  CuaTaskPublic,
  CuaTaskSummary,
} from "@/lib/api/generated/types.gen";

/**
 * CUA Tasks API Hooks
 *
 * Custom TanStack Query hooks for CUA (Computer Use Agent) task operations.
 * Handles cache invalidation and polling for running tasks.
 */

/**
 * Query key factory for CUA tasks
 */
export const cuaTasksQueryKeys = {
  all: ["cua-tasks"] as const,
  lists: () => [...cuaTasksQueryKeys.all, "list"] as const,
  list: (filters: { status?: string }) =>
    [...cuaTasksQueryKeys.lists(), filters] as const,
  active: () => [...cuaTasksQueryKeys.all, "active"] as const,
  details: () => [...cuaTasksQueryKeys.all, "detail"] as const,
  detail: (taskId: string) => [...cuaTasksQueryKeys.details(), taskId] as const,
};

/**
 * Fetch all CUA tasks with optional status filter and pagination
 */
export function useCuaTasks(options?: {
  status?: string;
  skip?: number;
  limit?: number;
}) {
  const { status, skip = 0, limit = 50 } = options || {};

  return useQuery({
    queryKey: cuaTasksQueryKeys.list({ status }),
    queryFn: async () => {
      const client = await getApiClient();
      const result = await CuaTasksService.listCuaTasks({
        client,
        query: { status, skip, limit },
      });
      if (!result.data) {
        throw new Error("Failed to fetch CUA tasks");
      }
      return result.data;
    },
    staleTime: 1000 * 30, // 30 seconds
  });
}

/**
 * Fetch active (pending or running) CUA tasks
 * Useful for showing currently running tasks
 */
export function useActiveCuaTasks(options?: { refetchInterval?: number }) {
  const { refetchInterval = 5000 } = options || {}; // Default 5 second polling

  return useQuery({
    queryKey: cuaTasksQueryKeys.active(),
    queryFn: async () => {
      const client = await getApiClient();
      const result = await CuaTasksService.listActiveCuaTasks({ client });
      if (!result.data) {
        throw new Error("Failed to fetch active CUA tasks");
      }
      return result.data;
    },
    staleTime: 1000 * 5, // 5 seconds - more aggressive for active tasks
    refetchInterval, // Poll for updates
  });
}

/**
 * Fetch a single CUA task by ID
 * Includes full step data
 * Automatically polls if task is running
 */
export function useCuaTask(taskId: string) {
  return useQuery({
    queryKey: cuaTasksQueryKeys.detail(taskId),
    queryFn: async () => {
      const client = await getApiClient();
      const result = await CuaTasksService.getCuaTask({
        client,
        path: { task_id: taskId },
      });
      if (!result.data) {
        throw new Error("Failed to fetch CUA task");
      }
      return result.data;
    },
    enabled: !!taskId,
    staleTime: 1000 * 5, // 5 seconds
    // Dynamic refetch interval: poll if task is running
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && isTaskRunning(data)) {
        return 3000; // Poll every 3 seconds for running tasks
      }
      return false;
    },
  });
}

/**
 * Stop a running CUA task
 */
export function useStopCuaTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: string) => {
      const client = await getApiClient();
      const result = await CuaTasksService.stopCuaTask({
        client,
        path: { task_id: taskId },
      });
      return result.data;
    },
    onSuccess: () => {
      // Invalidate all task queries to refetch
      queryClient.invalidateQueries({ queryKey: cuaTasksQueryKeys.all });
    },
  });
}

/**
 * Permanently delete a CUA task
 */
export function useDeleteCuaTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: string) => {
      const client = await getApiClient();
      const result = await CuaTasksService.deleteCuaTask({
        client,
        path: { task_id: taskId },
      });
      return result.data;
    },
    onSuccess: () => {
      // Invalidate all task queries to refetch
      queryClient.invalidateQueries({ queryKey: cuaTasksQueryKeys.all });
    },
  });
}

/**
 * Helper to determine if a task is currently running
 */
export function isTaskRunning(task: CuaTaskSummary | CuaTaskPublic): boolean {
  return task.status === "pending" || task.status === "running";
}

/**
 * Helper to get status color for UI
 */
export function getTaskStatusColor(
  status: string
): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "completed":
      return "default"; // green-ish in most shadcn themes
    case "running":
    case "pending":
      return "secondary"; // blue-ish
    case "failed":
    case "timeout":
      return "destructive"; // red
    case "stopped":
      return "outline"; // gray
    default:
      return "default";
  }
}

/**
 * Helper to get status display text
 */
export function getTaskStatusText(status: string): string {
  switch (status) {
    case "pending":
      return "Pending";
    case "running":
      return "Running";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    case "stopped":
      return "Stopped";
    case "timeout":
      return "Timed Out";
    default:
      return status;
  }
}

/**
 * Re-export types for convenience
 */
export type { CuaTaskPublic, CuaTaskSummary };
