import { useQuery } from "@tanstack/react-query";
import { getApiClient, ConversationsService } from "@/lib/api/client";
import type {
  ConversationPublic,
  ConversationSummary,
  ConversationWithTasks,
  ConversationMessagePublic,
} from "@/lib/api/generated/types.gen";

/**
 * Conversations API Hooks
 *
 * Custom TanStack Query hooks for conversation management.
 */

/**
 * Query key factory for conversations
 */
export const conversationsQueryKeys = {
  all: ["conversations"] as const,
  lists: () => [...conversationsQueryKeys.all, "list"] as const,
  list: (workspaceId: string, filters?: { status?: string }) =>
    [...conversationsQueryKeys.lists(), workspaceId, filters] as const,
  details: () => [...conversationsQueryKeys.all, "detail"] as const,
  detail: (conversationId: string) =>
    [...conversationsQueryKeys.details(), conversationId] as const,
  withTasks: (conversationId: string) =>
    [...conversationsQueryKeys.all, "with-tasks", conversationId] as const,
  messages: (conversationId: string) =>
    [...conversationsQueryKeys.all, "messages", conversationId] as const,
};

/**
 * Fetch conversations with summaries (message count, task count, last message)
 */
export function useConversations(
  workspaceId: string | undefined,
  options?: {
    status?: string;
    skip?: number;
    limit?: number;
  }
) {
  const { status, skip = 0, limit = 50 } = options || {};

  return useQuery({
    queryKey: conversationsQueryKeys.list(workspaceId || "", { status }),
    queryFn: async () => {
      if (!workspaceId) {
        throw new Error("Workspace ID is required");
      }
      const client = await getApiClient();
      const result =
        await ConversationsService.getWorkspaceConversationsWithSummaries({
          client,
          path: { workspace_id: workspaceId },
          query: { status, skip, limit },
        });
      if (!result.data) {
        throw new Error("Failed to fetch conversations");
      }
      return result.data;
    },
    enabled: !!workspaceId,
    staleTime: 1000 * 30, // 30 seconds
  });
}

/**
 * Fetch a single conversation by ID
 */
export function useConversation(conversationId: string | undefined) {
  return useQuery({
    queryKey: conversationsQueryKeys.detail(conversationId || ""),
    queryFn: async () => {
      if (!conversationId) {
        throw new Error("Conversation ID is required");
      }
      const client = await getApiClient();
      const result = await ConversationsService.getConversation({
        client,
        path: { conversation_id: conversationId },
      });
      if (!result.data) {
        throw new Error("Failed to fetch conversation");
      }
      return result.data;
    },
    enabled: !!conversationId,
    staleTime: 1000 * 30, // 30 seconds
  });
}

/**
 * Fetch a conversation with its associated tasks
 */
export function useConversationWithTasks(conversationId: string | undefined) {
  return useQuery({
    queryKey: conversationsQueryKeys.withTasks(conversationId || ""),
    queryFn: async () => {
      if (!conversationId) {
        throw new Error("Conversation ID is required");
      }
      const client = await getApiClient();
      const result = await ConversationsService.getConversationWithTasks({
        client,
        path: { conversation_id: conversationId },
      });
      if (!result.data) {
        throw new Error("Failed to fetch conversation with tasks");
      }
      return result.data;
    },
    enabled: !!conversationId,
    staleTime: 1000 * 30, // 30 seconds
  });
}

/**
 * Fetch messages for a conversation
 */
export function useConversationMessages(conversationId: string | undefined) {
  return useQuery({
    queryKey: conversationsQueryKeys.messages(conversationId || ""),
    queryFn: async () => {
      if (!conversationId) {
        throw new Error("Conversation ID is required");
      }
      const client = await getApiClient();
      const result = await ConversationsService.getConversationMessages({
        client,
        path: { conversation_id: conversationId },
      });
      if (!result.data) {
        throw new Error("Failed to fetch conversation messages");
      }
      return result.data;
    },
    enabled: !!conversationId,
    staleTime: 1000 * 10, // 10 seconds
  });
}

/**
 * Helper to get conversation status display text
 */
export function getConversationStatusText(status: string): string {
  switch (status) {
    case "active":
      return "Active";
    case "closed":
      return "Closed";
    case "resolved":
      return "Resolved";
    case "pending":
      return "Pending";
    default:
      return status;
  }
}

/**
 * Helper to get status color
 */
export function getConversationStatusColor(
  status: string
): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "active":
      return "default";
    case "closed":
      return "secondary";
    case "resolved":
      return "default";
    case "pending":
      return "outline";
    default:
      return "secondary";
  }
}

/**
 * Re-export types for convenience
 */
export type {
  ConversationPublic,
  ConversationSummary,
  ConversationWithTasks,
  ConversationMessagePublic,
};
