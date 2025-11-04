"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { PublicChatApi } from "@/lib/api/public/client";
import { env } from "@/lib/env";

export default function PublicChatPage() {
  const params = useParams<{ workspace_handle: string }>();
  const workspaceHandle = params.workspace_handle;

  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<
    Array<{ id: string; role: string; content: string; created_at: string }>
  >([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [streamText, setStreamText] = useState<string>("");
  const streamRef = useRef<EventSource | null>(null);

  // Create conversation once
  useEffect(() => {
    let mounted = true;
    (async () => {
      if (!workspaceHandle) return;
      const resp = await PublicChatApi.createConversation({
        workspace_handle: workspaceHandle,
      });
      if (!mounted) return;
      setConversationId(resp.conversation_id);
    })();
    return () => {
      mounted = false;
    };
  }, [workspaceHandle]);

  // Load initial messages on mount (no polling needed - each conversation is isolated)
  useEffect(() => {
    if (!conversationId) return;
    (async () => {
      try {
        const resp = await PublicChatApi.listMessages(conversationId, {
          limit: 50,
        });
        if (resp.messages.length > 0) {
          setMessages(
            resp.messages.map((m) => ({
              id: m.id,
              role: m.role,
              content: m.content,
              created_at: m.created_at,
            }))
          );
        }
      } catch {
        // swallow for MVP
      }
    })();
  }, [conversationId]);

  const sorted = useMemo(() => {
    return [...messages].sort((a, b) =>
      a.created_at.localeCompare(b.created_at)
    );
  }, [messages]);

  const send = async () => {
    if (!conversationId || !input.trim() || isSending) return;
    setIsSending(true);
    try {
      // Optimistically append the user message for immediate UI feedback
      const userContent = input.trim();
      const optimisticId = `local-user-${Date.now()}`;
      const optimisticUser = {
        id: optimisticId,
        role: "user",
        content: userContent,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => {
        const next = [...prev, optimisticUser];
        return next;
      });

      // Post message and get the real message back with its real ID
      const realMessage = await PublicChatApi.postMessage(conversationId, {
        role: "user",
        content: userContent,
      });

      // Replace optimistic message with real one immediately
      setMessages((prev) => {
        const next = [...prev];
        const optimisticIndex = next.findIndex(
          (msg) => msg.id === optimisticId
        );
        if (optimisticIndex !== -1) {
          next[optimisticIndex] = {
            id: realMessage.id,
            role: realMessage.role,
            content: realMessage.content,
            created_at: realMessage.created_at,
          };
        }
        return next;
      });

      setInput("");
      // Start SSE stream for assistant reply
      try {
        // Close previous stream if any
        if (streamRef.current) {
          streamRef.current.close();
          streamRef.current = null;
        }
        // Build API base (normalize to /api/v1 like our client)
        const base = (() => {
          const trimmed = env.NEXT_PUBLIC_API_URL.replace(/\/$/, "");
          return trimmed.endsWith("/api/v1") ? trimmed : `${trimmed}/api/v1`;
        })();
        const url = `${base}/public/conversations/${conversationId}/stream`;
        const es = new EventSource(url, { withCredentials: false });
        streamRef.current = es;
        setStreamText("");

        es.addEventListener("delta", (ev) => {
          try {
            const data = JSON.parse((ev as MessageEvent).data) as {
              text_chunk: string;
            };
            setStreamText((prev) => prev + (data.text_chunk || ""));
          } catch {
            // ignore parse errors
          }
        });
        es.addEventListener("message_end", async () => {
          try {
            if (conversationId) {
              const resp = await PublicChatApi.listMessages(conversationId, {
                limit: 50,
              });
              setMessages(
                resp.messages.map((m) => ({
                  id: m.id,
                  role: m.role,
                  content: m.content,
                  created_at: m.created_at,
                }))
              );
            }
            setStreamText("");
          } catch {
            setStreamText("");
          }
          es.close();
          streamRef.current = null;
        });
        es.addEventListener("error", () => {
          // On error, close stream
          if (streamRef.current) {
            streamRef.current.close();
            streamRef.current = null;
          }
          setStreamText("");
        });
      } catch {
        // Stream setup failed, but continue
      }
    } catch {
      // noop MVP
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-1 flex-col gap-4 p-4">
      <h1 className="text-xl font-semibold">Chat with {workspaceHandle}</h1>
      <Card className="flex min-h-[400px] flex-1 flex-col gap-2 p-3">
        <div className="flex-1 space-y-2 overflow-y-auto">
          {sorted.map((m) => (
            <div key={m.id} className="flex flex-col">
              <span className="text-xs text-muted-foreground">{m.role}</span>
              <span>{m.content}</span>
            </div>
          ))}
          {sorted.length === 0 && (
            <div className="text-sm text-muted-foreground">
              Say hi to start the conversation.
            </div>
          )}
          {streamText && (
            <div className="flex flex-col">
              <span className="text-xs text-muted-foreground">assistant</span>
              <span>{streamText}</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Input
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") send();
            }}
          />
          <Button onClick={send} disabled={!input.trim() || isSending}>
            {isSending ? "Sending..." : "Send"}
          </Button>
        </div>
      </Card>
    </div>
  );
}
