"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { PublicChatApi } from "@/lib/api/public/client";

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
  const pollRef = useRef<NodeJS.Timeout | null>(null);

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

  // Poll messages
  useEffect(() => {
    if (!conversationId) return;
    const poll = async () => {
      try {
        const resp = await PublicChatApi.listMessages(conversationId, {
          since: since ?? undefined,
          limit: 50,
        });
        if (resp.messages.length > 0) {
          setMessages((prev) => [
            ...prev,
            ...resp.messages.map((m) => ({
              id: m.id,
              role: m.role,
              content: m.content,
              created_at: m.created_at,
            })),
          ]);
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
      await PublicChatApi.postMessage(conversationId, {
        role: "user",
        content: input.trim(),
      });
      setInput("");
      // Force a poll right away
      setSince(null);
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
