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
  const [since, setSince] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [streamText, setStreamText] = useState<string>("");
  const pollRef = useRef<NodeJS.Timeout | null>(null);
  const streamRef = useRef<EventSource | null>(null);
  const isStreamingRef = useRef<boolean>(false);
  const seenMessageIdsRef = useRef<Set<string>>(new Set());

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

  // Poll messages (disabled while streaming)
  useEffect(() => {
    if (!conversationId) return;
    const poll = async () => {
      if (isStreamingRef.current) return; // pause polling during SSE
      try {
        const resp = await PublicChatApi.listMessages(conversationId, {
          since: since ?? undefined,
          limit: 50,
        });
        if (resp.messages.length > 0) {
          setMessages((prev) => {
            const next = [...prev];
            for (const m of resp.messages) {
              if (!seenMessageIdsRef.current.has(m.id)) {
                next.push({
                  id: m.id,
                  role: m.role,
                  content: m.content,
                  created_at: m.created_at,
                });
                seenMessageIdsRef.current.add(m.id);
              }
            }
            return next;
          });
          if (resp.next_since) setSince(resp.next_since);
        }
      } catch {
        // swallow for MVP
      }
    };
    // initial fetch
    poll();
    pollRef.current = setInterval(poll, 2500);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [conversationId, since]);

  const sorted = useMemo(() => {
    return [...messages].sort((a, b) =>
      a.created_at.localeCompare(b.created_at)
    );
  }, [messages]);

  const send = async () => {
    if (!conversationId || !input.trim() || isSending) return;
    setIsSending(true);
    try {
      // Optimistically append the user message
      const nowIso = new Date().toISOString();
      const optimisticUser = {
        id: `local-user-${Date.now()}`,
        role: "user",
        content: input.trim(),
        created_at: nowIso,
      };
      setMessages((prev) => {
        const next = [...prev, optimisticUser];
        return next;
      });
      seenMessageIdsRef.current.add(optimisticUser.id);

      await PublicChatApi.postMessage(conversationId, {
        role: "user",
        content: input.trim(),
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
        isStreamingRef.current = true;

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
        es.addEventListener("message_end", (ev) => {
          try {
            const data = JSON.parse((ev as MessageEvent).data) as {
              full_text: string;
            };
            // Clear streaming text and trigger polling refresh
            const text = data.full_text || "";
            setStreamText("");
            // Optimistically append assistant final message so UI doesn't flicker blank
            if (text) {
              const optimisticAssistant = {
                id: `local-assistant-${Date.now()}`,
                role: "assistant",
                content: text,
                created_at: new Date().toISOString(),
              };
              setMessages((prev) => [...prev, optimisticAssistant]);
            }
            // trigger one immediate poll after stream ends
            isStreamingRef.current = false;
            // do not reset since; next poll will fetch only new items
          } catch {
            setStreamText("");
            isStreamingRef.current = false;
          }
          es.close();
          streamRef.current = null;
        });
        es.addEventListener("error", () => {
          // On error, close and fallback to polling
          if (streamRef.current) {
            streamRef.current.close();
            streamRef.current = null;
          }
          setStreamText("");
          isStreamingRef.current = false;
        });
      } catch {
        // Fallback to polling
        isStreamingRef.current = false;
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
