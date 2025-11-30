"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  MessageSquare,
  Clock,
  User,
  Mail,
  CheckCircle,
  Layers,
} from "lucide-react";
import type { ConversationSummary } from "@/lib/api/hooks/use-conversations";

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

interface ConversationCardProps {
  conversation: ConversationSummary;
  className?: string;
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
    <Badge variant="outline" className={cn("font-medium", config.className)}>
      {config.label}
    </Badge>
  );
}

export function ConversationCard({
  conversation,
  className,
}: ConversationCardProps) {
  const isActive = conversation.status === "active";

  return (
    <Link href={`/conversations/${conversation.id}`}>
      <Card
        className={cn(
          "hover:shadow-md transition-all cursor-pointer",
          isActive && "ring-1 ring-green-500/20",
          className
        )}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base font-medium flex items-center gap-2">
                {conversation.visitor_name ? (
                  <>
                    <User className="h-4 w-4 text-muted-foreground" />
                    {conversation.visitor_name}
                  </>
                ) : (
                  <>
                    <User className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Anonymous</span>
                  </>
                )}
              </CardTitle>
              {conversation.visitor_email && (
                <CardDescription className="mt-1 flex items-center gap-1 text-xs">
                  <Mail className="h-3 w-3" />
                  {conversation.visitor_email}
                </CardDescription>
              )}
            </div>
            <StatusBadge status={conversation.status} />
          </div>
        </CardHeader>
        <CardContent className="pt-0 space-y-3">
          {/* Last message preview */}
          {conversation.last_message_content && (
            <div className="p-2 bg-muted/50 rounded-md">
              <div className="flex items-center gap-1 text-xs text-muted-foreground mb-1">
                {conversation.last_message_role === "assistant" ? (
                  <CheckCircle className="h-3 w-3" />
                ) : (
                  <User className="h-3 w-3" />
                )}
                <span className="capitalize">
                  {conversation.last_message_role}
                </span>
                {conversation.last_message_at && (
                  <>
                    <span className="mx-1">•</span>
                    <span>{formatTimeAgo(conversation.last_message_at)}</span>
                  </>
                )}
              </div>
              <p className="text-sm text-foreground/80 line-clamp-2">
                {conversation.last_message_content}
              </p>
            </div>
          )}

          {/* Stats row */}
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <MessageSquare className="h-3 w-3" />
                {conversation.message_count} messages
              </span>
              {(conversation.task_count ?? 0) > 0 && (
                <span className="flex items-center gap-1 text-blue-600">
                  <Layers className="h-3 w-3" />
                  {conversation.task_count ?? 0} task
                  {(conversation.task_count ?? 0) > 1 ? "s" : ""}
                </span>
              )}
            </div>
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatTimeAgo(conversation.created_at)}
            </span>
          </div>

          {/* Tags */}
          {conversation.tags && conversation.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {conversation.tags.slice(0, 3).map((tag) => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {conversation.tags.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{conversation.tags.length - 3}
                </Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
