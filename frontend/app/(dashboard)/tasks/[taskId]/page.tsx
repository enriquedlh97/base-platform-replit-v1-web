"use client";

import { useState } from "react";
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
import { TaskStatusBadge } from "@/components/tasks/task-status-badge";
import { TaskStepCard, type TaskStep } from "@/components/tasks/task-step-card";
import { TaskTimeline } from "@/components/tasks/task-timeline";
import {
  useCuaTask,
  useStopCuaTask,
  isTaskRunning,
} from "@/lib/api/hooks/use-cua-tasks";
import {
  ArrowLeft,
  Bot,
  Clock,
  Layers,
  RefreshCw,
  Square,
  AlertTriangle,
  CheckCircle2,
  MessageSquare,
} from "lucide-react";

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

// Type for task metadata
interface TaskMetadata {
  duration?: number;
  input_tokens_used?: number;
  output_tokens_used?: number;
  max_steps?: number;
  number_of_steps?: number;
}

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.taskId as string;

  const [selectedStepIndex, setSelectedStepIndex] = useState<number | null>(
    null
  );

  // Fetch task - automatically polls if task is running
  const {
    data: task,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useCuaTask(taskId);

  const stopTask = useStopCuaTask();

  const handleStopTask = async () => {
    if (task && isTaskRunning(task)) {
      await stopTask.mutateAsync(task.id);
    }
  };

  // Get selected step or latest step - convert from API format to component format
  const steps: TaskStep[] = (task?.steps ?? []).map((step) => ({
    step_id: String(step.stepId ?? step.step_id ?? ""),
    image: step.image as string | undefined,
    thought: step.thought as string | undefined,
    actions: step.actions as TaskStep["actions"],
    error: step.error as string | undefined,
    duration: step.duration as number | undefined,
    input_tokens_used: step.inputTokensUsed as number | undefined,
    output_tokens_used: step.outputTokensUsed as number | undefined,
  }));

  // Get task metadata with proper typing
  const taskMetadata = (task?.task_metadata ?? {}) as TaskMetadata;
  const selectedStep =
    selectedStepIndex !== null
      ? steps[selectedStepIndex]
      : steps[steps.length - 1];

  // Get final answer from last step if available
  const getFinalAnswer = () => {
    if (!steps.length) return null;
    const lastStep = steps[steps.length - 1];
    const finalAction = lastStep.actions?.find(
      (a) => a.function_name === "final_answer"
    );
    if (finalAction) {
      return (
        (finalAction.parameters.answer as string) ||
        (finalAction.parameters.arg_0 as string)
      );
    }
    return null;
  };

  const finalAnswer = getFinalAnswer();

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
            <h2 className="text-xl font-semibold mb-2">Task Not Found</h2>
            <p className="text-muted-foreground mb-4">
              The task you&apos;re looking for doesn&apos;t exist or you
              don&apos;t have access to it.
            </p>
            <Button onClick={() => router.push("/tasks")}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Tasks
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
              {/* Back button and header */}
              <div className="flex items-center gap-4">
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/tasks">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back
                  </Link>
                </Button>
              </div>

              {isLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-8 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-64 w-full" />
                </div>
              ) : task ? (
                <>
                  {/* Task Header */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <TaskStatusBadge status={task.status} />
                        {isTaskRunning(task) && (
                          <Badge
                            variant="outline"
                            className="gap-1 text-blue-600"
                          >
                            <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
                            Live
                          </Badge>
                        )}
                      </div>
                      <h1 className="text-xl font-semibold mb-2">
                        {task.instruction}
                      </h1>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          {formatTimeAgo(task.started_at)}
                        </span>
                        <span className="flex items-center gap-1">
                          <Layers className="h-4 w-4" />
                          {steps.length} steps
                        </span>
                        <span className="flex items-center gap-1">
                          <Bot className="h-4 w-4" />
                          {task.model_id.split("/").pop()}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => refetch()}
                        disabled={isFetching}
                      >
                        <RefreshCw
                          className={`h-4 w-4 mr-2 ${
                            isFetching ? "animate-spin" : ""
                          }`}
                        />
                        Refresh
                      </Button>
                      {isTaskRunning(task) && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={handleStopTask}
                          disabled={stopTask.isPending}
                        >
                          <Square className="h-4 w-4 mr-2" />
                          Stop
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Task Metadata */}
                  {taskMetadata && (
                    <div className="flex items-center gap-4 text-sm">
                      {taskMetadata.duration && taskMetadata.duration > 0 && (
                        <Badge variant="secondary">
                          Duration: {taskMetadata.duration.toFixed(1)}s
                        </Badge>
                      )}
                      {((taskMetadata.input_tokens_used ?? 0) > 0 ||
                        (taskMetadata.output_tokens_used ?? 0) > 0) && (
                        <Badge variant="secondary">
                          Tokens:{" "}
                          {(
                            (taskMetadata.input_tokens_used ?? 0) +
                            (taskMetadata.output_tokens_used ?? 0)
                          ).toLocaleString()}
                        </Badge>
                      )}
                    </div>
                  )}

                  {/* Error message */}
                  {task.error_message && (
                    <Card className="border-red-500/20 bg-red-500/5">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base text-red-600 flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4" />
                          Error
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm">{task.error_message}</p>
                      </CardContent>
                    </Card>
                  )}

                  {/* Final Answer */}
                  {finalAnswer && task.status === "completed" && (
                    <Card className="border-green-500/20 bg-green-500/5">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base text-green-600 flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4" />
                          Task Completed
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-start gap-2">
                          <MessageSquare className="h-4 w-4 mt-0.5 text-muted-foreground" />
                          <p className="text-sm">{finalAnswer}</p>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Timeline */}
                  {steps.length > 0 && (
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium">
                          Timeline
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <TaskTimeline
                          steps={steps}
                          status={task.status}
                          selectedStepIndex={selectedStepIndex}
                          onStepSelect={setSelectedStepIndex}
                        />
                      </CardContent>
                    </Card>
                  )}

                  {/* Main content - Screenshot and Steps */}
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    {/* Screenshot viewer */}
                    <div className="lg:col-span-2">
                      <Card className="h-full">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium flex items-center justify-between">
                            <span>
                              {selectedStepIndex !== null
                                ? `Step ${selectedStepIndex + 1} Screenshot`
                                : steps.length > 0
                                  ? `Latest Screenshot (Step ${steps.length})`
                                  : "No Screenshots Yet"}
                            </span>
                            {isTaskRunning(task) && (
                              <Badge
                                variant="outline"
                                className="text-blue-600"
                              >
                                <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse mr-1" />
                                LIVE
                              </Badge>
                            )}
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          {selectedStep?.image ? (
                            <div className="relative bg-black rounded-lg overflow-hidden">
                              {/* eslint-disable-next-line @next/next/no-img-element */}
                              <img
                                src={selectedStep.image}
                                alt={`Step ${
                                  selectedStepIndex !== null
                                    ? selectedStepIndex + 1
                                    : steps.length
                                }`}
                                className="w-full h-auto"
                              />
                            </div>
                          ) : (
                            <div className="flex items-center justify-center h-64 bg-muted rounded-lg">
                              <p className="text-muted-foreground">
                                {isTaskRunning(task)
                                  ? "Waiting for first screenshot..."
                                  : "No screenshot available"}
                              </p>
                            </div>
                          )}

                          {/* Step thought */}
                          {selectedStep?.thought && (
                            <div className="mt-4 p-3 bg-muted rounded-lg">
                              <p className="text-sm font-medium mb-1">
                                Agent Thought:
                              </p>
                              <p className="text-sm text-muted-foreground">
                                {selectedStep.thought}
                              </p>
                            </div>
                          )}

                          {/* Step actions */}
                          {selectedStep?.actions &&
                            selectedStep.actions.length > 0 && (
                              <div className="mt-4">
                                <p className="text-sm font-medium mb-2">
                                  Actions:
                                </p>
                                <div className="flex flex-wrap gap-2">
                                  {selectedStep.actions.map((action, i) => (
                                    <Badge key={i} variant="outline">
                                      {action.description ||
                                        action.function_name}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                        </CardContent>
                      </Card>
                    </div>

                    {/* Steps list */}
                    <div className="lg:col-span-1">
                      <Card className="h-full">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm font-medium">
                            Steps ({steps.length}
                            {taskMetadata.max_steps
                              ? `/${taskMetadata.max_steps}`
                              : ""}
                            )
                          </CardTitle>
                          <CardDescription>
                            Click a step to view its screenshot
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="p-0">
                          <ScrollArea className="h-[500px]">
                            <div className="p-4 space-y-2">
                              {steps.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">
                                  {isTaskRunning(task)
                                    ? "Waiting for steps..."
                                    : "No steps recorded"}
                                </div>
                              ) : (
                                steps.map((step, index) => (
                                  <TaskStepCard
                                    key={step.step_id}
                                    step={step}
                                    stepNumber={index + 1}
                                    isSelected={selectedStepIndex === index}
                                    onClick={() => setSelectedStepIndex(index)}
                                  />
                                ))
                              )}
                            </div>
                          </ScrollArea>
                        </CardContent>
                      </Card>
                    </div>
                  </div>

                  {/* Task completion info */}
                  {task.completed_at && (
                    <div className="text-sm text-muted-foreground">
                      Completed {formatDate(task.completed_at)}
                    </div>
                  )}
                </>
              ) : null}
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
