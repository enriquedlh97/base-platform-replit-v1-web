export interface CreateConversationRequest {
  workspace_handle: string;
  idempotency_key?: string;
}

export interface CreateConversationResponse {
  conversation_id: string;
  created_at: string;
}

export interface PostMessageRequest {
  role: string;
  content: string;
  idempotency_key?: string;
}

export interface ConversationMessagePublic {
  id: string;
  conversation_id: string;
  content: string;
  role: string;
  timestamp: string;
  created_at: string;
}

export interface ListMessagesResponse {
  messages: ConversationMessagePublic[];
  next_since: string | null;
}

import { env } from "@/lib/env";

function ensureApiV1Base(url: string): string {
  const trimmed = url.replace(/\/$/, "");
  if (trimmed.endsWith("/api/v1")) return trimmed;
  return `${trimmed}/api/v1`;
}

const API_BASE = ensureApiV1Base(env.NEXT_PUBLIC_API_URL);

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed with ${res.status}`);
  }
  return (await res.json()) as T;
}

export const PublicChatApi = {
  createConversation: (body: CreateConversationRequest) =>
    http<CreateConversationResponse>(`/public/conversations`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  postMessage: (conversationId: string, body: PostMessageRequest) =>
    http<ConversationMessagePublic>(
      `/public/conversations/${conversationId}/messages`,
      { method: "POST", body: JSON.stringify(body) }
    ),
  listMessages: (
    conversationId: string,
    params?: { since?: string; limit?: number }
  ) => {
    const qs = new URLSearchParams();
    if (params?.since) qs.set("since", params.since);
    if (params?.limit) qs.set("limit", String(params.limit));
    const suffix = qs.toString() ? `?${qs.toString()}` : "";
    return http<ListMessagesResponse>(
      `/public/conversations/${conversationId}/messages${suffix}`
    );
  },
};
