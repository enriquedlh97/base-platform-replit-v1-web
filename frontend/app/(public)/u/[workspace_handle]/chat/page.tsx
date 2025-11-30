"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  PublicChatApi,
  type WorkspaceProfilePublic,
} from "@/lib/api/public/client";
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
  const [toolStatus, setToolStatus] = useState<{
    tool: string;
    status: "calling" | "executing" | "completed" | "error";
    message?: string;
  } | null>(null);
  const [hasReceivedText, setHasReceivedText] = useState(false);
  const [workspaceProfile, setWorkspaceProfile] =
    useState<WorkspaceProfilePublic | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const streamRef = useRef<EventSource | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Fetch workspace profile
  useEffect(() => {
    let mounted = true;
    (async () => {
      if (!workspaceHandle) return;
      try {
        setProfileLoading(true);
        const profile =
          await PublicChatApi.getWorkspaceProfile(workspaceHandle);
        if (!mounted) return;
        setWorkspaceProfile(profile);
      } catch (error) {
        console.error("Failed to load workspace profile:", error);
        // Continue without profile - will use fallback
      } finally {
        if (mounted) {
          setProfileLoading(false);
        }
      }
    })();
    return () => {
      mounted = false;
    };
  }, [workspaceHandle]);

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

  // Auto-scroll to bottom when messages change or streaming updates
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [sorted, streamText]);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const scrollHeight = textareaRef.current.scrollHeight;
      const maxHeight = 200; // Max height in pixels (about 8-10 lines)
      textareaRef.current.style.height = `${Math.min(scrollHeight, maxHeight)}px`;
      if (scrollHeight > maxHeight) {
        textareaRef.current.style.overflowY = "auto";
      } else {
        textareaRef.current.style.overflowY = "hidden";
      }
    }
  }, [input]);

  const send = async () => {
    if (!conversationId || !input.trim() || isSending) return;
    setIsSending(true);
    try {
      // Optimistically append the user message for immediate UI feedback
      // Preserve line breaks but trim trailing whitespace
      const userContent = input.replace(/\s+$/, "");
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
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
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
        setHasReceivedText(false);
        setToolStatus(null); // Clear tool status when starting a new message

        es.addEventListener("delta", (ev) => {
          try {
            const data = JSON.parse((ev as MessageEvent).data) as {
              text_chunk: string;
            };
            setStreamText((prev) => prev + (data.text_chunk || ""));
            // Mark that we've received text - this allows tool status to appear after text
            if (data.text_chunk) {
              setHasReceivedText(true);
            }
            // Don't clear tool status - keep it visible to show completion
            // The tool status will be updated to "completed" when tool_result arrives
          } catch {
            // ignore parse errors
          }
        });

        es.addEventListener("tool_call", (ev) => {
          try {
            const data = JSON.parse((ev as MessageEvent).data) as {
              id: string;
              tool: string;
              args: Record<string, unknown>;
            };
            // Only show tool status after we've received some text (pre-message)
            // This ensures the pre-message appears before the tool status
            // Use a small delay to ensure text is rendered first
            const showToolStatus = () => {
              if (data.tool === "schedule_appointment_with_cua") {
                setToolStatus({
                  tool: data.tool,
                  status: "calling",
                  message: "I'm scheduling your appointment...",
                });
              } else {
                setToolStatus({
                  tool: data.tool,
                  status: "calling",
                  message: `Using ${data.tool}...`,
                });
              }
            };

            // If we've already received text, show immediately
            // Otherwise, wait a bit for text to render first
            if (hasReceivedText) {
              showToolStatus();
            } else {
              // Wait a short time for text to start rendering
              setTimeout(showToolStatus, 100);
            }
          } catch {
            // ignore parse errors
          }
        });

        es.addEventListener("tool_result", (ev) => {
          try {
            const data = JSON.parse((ev as MessageEvent).data) as {
              id: string;
              status: string;
              data: string | null;
              error: string | null;
            };
            // Check if the tool result indicates success or failure
            // The status field tells us, and we can also check the data/error
            const isSuccess = data.status === "success" && !data.error;

            if (isSuccess) {
              // Update status to completed (green indicator) but keep it visible
              setToolStatus((prev) => {
                if (prev) {
                  return {
                    ...prev,
                    status: "completed",
                    message: "Appointment scheduled successfully!",
                  };
                }
                return {
                  tool: "schedule_appointment_with_cua",
                  status: "completed",
                  message: "Appointment scheduled successfully!",
                };
              });
              // Don't clear - keep it visible so user knows it completed
            } else {
              // Failed - show red indicator with user-friendly message
              // Don't show technical error details, just a simple failure message
              setToolStatus((prev) => {
                if (prev) {
                  return {
                    ...prev,
                    status: "error",
                    message: "Failed to schedule appointment",
                  };
                }
                return {
                  tool: "schedule_appointment_with_cua",
                  status: "error",
                  message: "Failed to schedule appointment",
                };
              });
            }
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
              const updatedMessages = resp.messages.map((m) => ({
                id: m.id,
                role: m.role,
                content: m.content,
                created_at: m.created_at,
              }));
              setMessages(updatedMessages);
            }
            setStreamText("");
            // Keep tool status visible - it will be cleared when a new message starts
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
          // Don't clear tool status on error - keep it visible to show what happened
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

  // Get display name - use profile public_name, fallback to handle
  const displayName = workspaceProfile?.public_name || workspaceHandle;
  const displayNameCapitalized = displayName
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-4 overflow-hidden p-4">
        {/* Profile Header */}
        {!profileLoading && workspaceProfile && (
          <div className="flex-shrink-0 space-y-4 rounded-lg border bg-card p-6">
            <div className="flex items-start gap-4">
              <Avatar className="h-16 w-16 flex-shrink-0">
                <AvatarImage
                  src={workspaceProfile.profile_image_url || undefined}
                  alt={displayNameCapitalized}
                />
                <AvatarFallback className="text-lg">
                  {displayNameCapitalized
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .toUpperCase()
                    .slice(0, 2)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-bold">
                    {displayNameCapitalized}
                  </h1>
                  <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    <span>Available to chat</span>
                  </div>
                </div>
                {workspaceProfile.subtitle && (
                  <p className="text-base text-muted-foreground">
                    {workspaceProfile.subtitle}
                  </p>
                )}
                {workspaceProfile.description && (
                  <p className="mt-2 text-sm text-muted-foreground">
                    {workspaceProfile.description}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
        {profileLoading && (
          <div className="flex-shrink-0">
            <div className="h-24 w-full animate-pulse rounded-lg bg-muted" />
          </div>
        )}
        {!profileLoading && !workspaceProfile && (
          <h1 className="flex-shrink-0 text-xl font-semibold">
            Chat with {workspaceHandle}
          </h1>
        )}
        <Card className="flex min-h-0 flex-1 flex-col gap-2 overflow-hidden p-4">
          <div
            ref={messagesContainerRef}
            className="flex min-h-0 flex-1 flex-col space-y-4 overflow-y-auto px-2"
          >
            {sorted.length === 0 && (
              <div className="flex h-full items-center justify-center">
                <div className="text-center">
                  <p className="text-lg font-medium text-foreground">
                    Welcome!
                  </p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {workspaceProfile?.public_name
                      ? `I'm an AI assistant representing ${workspaceProfile.public_name}. Ask me anything!`
                      : "Say hi to start the conversation."}
                  </p>
                </div>
              </div>
            )}
            {sorted.map((m) => (
              <div
                key={m.id}
                className={`flex w-full ${
                  m.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                    m.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground"
                  }`}
                >
                  <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                    {m.content}
                  </p>
                </div>
              </div>
            ))}
            {/* Show streaming text while message is being generated */}
            {streamText && (
              <div className="flex w-full justify-start">
                <div className="max-w-[85%] rounded-2xl bg-muted px-4 py-3 text-foreground">
                  <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                    {streamText}
                  </p>
                </div>
              </div>
            )}
            {/* Show tool status indicator */}
            {toolStatus && (
              <div className="flex w-full justify-start">
                <div className="flex items-center gap-2 rounded-lg bg-muted px-3 py-2">
                  {toolStatus.status === "calling" && (
                    <div className="h-2 w-2 animate-pulse rounded-full bg-blue-500" />
                  )}
                  {toolStatus.status === "executing" && (
                    <div className="h-2 w-2 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
                  )}
                  {toolStatus.status === "completed" && (
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                  )}
                  {toolStatus.status === "error" && (
                    <div className="h-2 w-2 rounded-full bg-red-500" />
                  )}
                  <span className="text-xs text-muted-foreground">
                    {toolStatus.message}
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="flex-shrink-0 border-t pt-4">
            <div className="flex items-end gap-2">
              <Textarea
                ref={textareaRef}
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    send();
                  }
                }}
                className="max-h-[200px] min-h-[40px] resize-none overflow-y-auto"
                rows={1}
              />
              <Button
                onClick={send}
                disabled={!input.trim() || isSending}
                size="icon"
              >
                {isSending ? (
                  <span className="text-sm">...</span>
                ) : (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="h-4 w-4"
                  >
                    <path d="m22 2-7 20-4-9-9-4Z" />
                    <path d="M22 2 11 13" />
                  </svg>
                )}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
