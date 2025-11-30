"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { MessageBubble } from "@/components/conversations/message-bubble";
import { TaskStatusBadge } from "@/components/tasks/task-status-badge";
import {
  useConversationWithTasks,
  useConversationMessages,
} from "@/lib/api/hooks/use-conversations";
import {
  ArrowLeft,
  User,
  Mail,
  Clock,
  MessageSquare,
  Layers,
  AlertTriangle,
  ExternalLink,
} from "lucide-react";
import type { CuaTaskSummary } from "@/lib/api/generated/types.gen";

// Helper to format date
function formatDate(date: string): string {
  return new Date(date).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

// Helper to format relative time
function formatTimeAgo(date: string): string {
  const seconds = Math.floor(
    (new Date().getTime() - new Date(date).getTime()) / 1000
  );
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function StatusBadge({ status }: { status: string }) {
  const config = {
    active: {
      label: "Active",
      className: "bg-green-500/10 text-green-600 border-green-500/20",
    },
    closed: {
      label: "Closed",
      className: "bg-gray-500/10 text-gray-600 border-gray-500/20",
    },
    resolved: {
      label: "Resolved",
      className: "bg-blue-500/10 text-blue-600 border-blue-500/20",
    },
    pending: {
      label: "Pending",
      className: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
    },
  }[status] || {
    label: status,
    className: "",
  };

  return (
    <Badge variant="outline" className={`font-medium ${config.className}`}>
      {config.label}
    </Badge>
  );
}

export default function ConversationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const conversationId = params.conversationId as string;

  // Fetch conversation with tasks
  const {
    data: conversation,
    isLoading: isLoadingConversation,
    error,
  } = useConversationWithTasks(conversationId);

  // Fetch messages
  const { data: messages, isLoading: isLoadingMessages } =
    useConversationMessages(conversationId);

  const isLoading = isLoadingConversation || isLoadingMessages;

  if (error) {
    return (
      <SidebarProvider
        style={
          {
            "--sidebar-width": "calc(var(--spacing) * 72)",
            "--header-height": "calc(var(--spacing) * 12)",
          } as React.CSSProperties
        }
      >
        <AppSidebar variant="inset" />
        <SidebarInset>
          <SiteHeader />
          <div className="flex flex-1 flex-col items-center justify-center p-8">
            <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
            <h2 className="text-xl font-semibold mb-2">
              Conversation Not Found
            </h2>
            <p className="text-muted-foreground mb-4">
              The conversation you&apos;re looking for doesn&apos;t exist or you
              don&apos;t have access to it.
            </p>
            <Button onClick={() => router.push("/conversations")}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Conversations
            </Button>
          </div>
        </SidebarInset>
      </SidebarProvider>
    );
  }

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar variant="inset" />
      <SidebarInset>
        <SiteHeader />
        <div className="flex flex-1 flex-col">
          <div className="@container/main flex flex-1 flex-col">
            <div className="flex flex-col gap-4 py-4 px-4 md:py-6 lg:px-6">
              {/* Back button */}
              <div className="flex items-center gap-4">
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/conversations">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back
                  </Link>
                </Button>
              </div>

              {isLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-8 w-1/3" />
                  <Skeleton className="h-4 w-1/4" />
                  <Skeleton className="h-64 w-full" />
                </div>
              ) : conversation ? (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Messages section */}
                  <div className="lg:col-span-2 space-y-4">
                    {/* Conversation header */}
                    <Card>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="space-y-1">
                            <CardTitle className="flex items-center gap-2">
                              {conversation.visitor_name ? (
                                <>
                                  <User className="h-5 w-5" />
                                  {conversation.visitor_name}
                                </>
                              ) : (
                                <>
                                  <User className="h-5 w-5 text-muted-foreground" />
                                  <span className="text-muted-foreground">
                                    Anonymous Visitor
                                  </span>
                                </>
                              )}
                            </CardTitle>
                            {conversation.visitor_email && (
                              <CardDescription className="flex items-center gap-1">
                                <Mail className="h-4 w-4" />
                                {conversation.visitor_email}
                              </CardDescription>
                            )}
                          </div>
                          <StatusBadge status={conversation.status} />
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground mt-2">
                          <span className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            Started {formatDate(conversation.created_at)}
                          </span>
                          <span className="flex items-center gap-1">
                            <MessageSquare className="h-4 w-4" />
                            {messages?.length || 0} messages
                          </span>
                        </div>
                      </CardHeader>
                    </Card>

                    {/* Messages */}
                    <Card className="flex flex-col h-[600px]">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">Messages</CardTitle>
                      </CardHeader>
                      <CardContent className="flex-1 overflow-hidden">
                        <ScrollArea className="h-full pr-4">
                          <div className="space-y-4 py-2">
                            {messages && messages.length > 0 ? (
                              messages.map((message) => (
                                <MessageBubble
                                  key={message.id}
                                  message={message}
                                />
                              ))
                            ) : (
                              <div className="flex items-center justify-center h-32 text-muted-foreground">
                                No messages yet
                              </div>
                            )}
                          </div>
                        </ScrollArea>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Sidebar - Tasks and info */}
                  <div className="space-y-4">
                    {/* Tasks section */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base flex items-center gap-2">
                          <Layers className="h-4 w-4" />
                          Related Tasks
                          {conversation.tasks &&
                            conversation.tasks.length > 0 && (
                              <Badge variant="secondary" className="ml-auto">
                                {conversation.tasks.length}
                              </Badge>
                            )}
                        </CardTitle>
                        <CardDescription>
                          Tasks triggered from this conversation
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        {conversation.tasks && conversation.tasks.length > 0 ? (
                          <div className="space-y-3">
                            {conversation.tasks.map((task: CuaTaskSummary) => (
                              <Link
                                key={task.id}
                                href={`/tasks/${task.id}`}
                                className="block"
                              >
                                <div className="p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                                  <div className="flex items-start justify-between gap-2 mb-2">
                                    <TaskStatusBadge status={task.status} />
                                    <ExternalLink className="h-4 w-4 text-muted-foreground" />
                                  </div>
                                  <p className="text-sm line-clamp-2 mb-2">
                                    {task.instruction.length > 80
                                      ? `${task.instruction.slice(0, 80)}...`
                                      : task.instruction}
                                  </p>
                                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                    <span>{task.step_count} steps</span>
                                    <span>•</span>
                                    <span>
                                      {formatTimeAgo(task.started_at)}
                                    </span>
                                  </div>
                                </div>
                              </Link>
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-6 text-muted-foreground">
                            <Layers className="h-8 w-8 mx-auto mb-2 opacity-50" />
                            <p className="text-sm">No tasks triggered yet</p>
                          </div>
                        )}
                      </CardContent>
                    </Card>

                    {/* Conversation details */}
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Details</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Channel</span>
                          <span className="capitalize">
                            {conversation.channel.replace("_", " ")}
                          </span>
                        </div>
                        <Separator />
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Created</span>
                          <span>{formatDate(conversation.created_at)}</span>
                        </div>
                        <Separator />
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">
                            Last updated
                          </span>
                          <span>{formatTimeAgo(conversation.updated_at)}</span>
                        </div>
                        {conversation.human_time_saved_minutes && (
                          <>
                            <Separator />
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">
                                Time saved
                              </span>
                              <span>
                                {conversation.human_time_saved_minutes} min
                              </span>
                            </div>
                          </>
                        )}
                      </CardContent>
                    </Card>

                    {/* Tags */}
                    {conversation.tags && conversation.tags.length > 0 && (
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-base">Tags</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="flex flex-wrap gap-2">
                            {conversation.tags.map((tag) => (
                              <Badge key={tag} variant="secondary">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
