"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { TaskStatusBadge } from "./task-status-badge";
import type { CuaTaskSummary } from "@/lib/api/hooks/use-cua-tasks";
import { Bot, Clock, Layers } from "lucide-react";
import { cn } from "@/lib/utils";

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

// Type for task metadata
interface TaskMetadata {
  duration?: number;
  input_tokens_used?: number;
  output_tokens_used?: number;
}

interface TaskCardProps {
  task: CuaTaskSummary;
  className?: string;
}

export function TaskCard({ task, className }: TaskCardProps) {
  const isRunning = task.status === "pending" || task.status === "running";
  const taskMetadata = (task.task_metadata ?? {}) as TaskMetadata;

  return (
    <Link href={`/tasks/${task.id}`}>
      <Card
        className={cn(
          "hover:shadow-md transition-all cursor-pointer",
          isRunning && "ring-2 ring-blue-500/20",
          className
        )}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base font-medium truncate">
                {task.instruction.length > 80
                  ? `${task.instruction.slice(0, 80)}...`
                  : task.instruction}
              </CardTitle>
              <CardDescription className="mt-1.5 flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatTimeAgo(task.started_at)}
                </span>
                <span className="flex items-center gap-1">
                  <Layers className="h-3 w-3" />
                  {task.step_count} steps
                </span>
              </CardDescription>
            </div>
            <TaskStatusBadge status={task.status} />
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Bot className="h-3 w-3" />
              <span className="truncate max-w-[200px]">{task.model_id}</span>
            </div>
            {taskMetadata && (
              <div className="flex items-center gap-3">
                {taskMetadata.duration && taskMetadata.duration > 0 && (
                  <span>{taskMetadata.duration.toFixed(1)}s</span>
                )}
                {((taskMetadata.input_tokens_used ?? 0) > 0 ||
                  (taskMetadata.output_tokens_used ?? 0) > 0) && (
                  <span>
                    {(
                      (taskMetadata.input_tokens_used ?? 0) +
                      (taskMetadata.output_tokens_used ?? 0)
                    ).toLocaleString()}{" "}
                    tokens
                  </span>
                )}
              </div>
            )}
          </div>
          {task.error_message && (
            <p className="mt-2 text-xs text-red-500 truncate">
              {task.error_message}
            </p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
