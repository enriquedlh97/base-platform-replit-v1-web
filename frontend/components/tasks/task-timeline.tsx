"use client";

import { cn } from "@/lib/utils";
import { CheckCircle, Loader2, XCircle, Square } from "lucide-react";
import type { TaskStep } from "./task-step-card";

interface TaskTimelineProps {
  steps: TaskStep[];
  status: string;
  selectedStepIndex: number | null;
  onStepSelect: (index: number | null) => void;
  className?: string;
}

export function TaskTimeline({
  steps,
  status,
  selectedStepIndex,
  onStepSelect,
  className,
}: TaskTimelineProps) {
  const isRunning = status === "running" || status === "pending";
  const isCompleted = status === "completed";
  const isFailed = status === "failed" || status === "timeout";
  const isStopped = status === "stopped";

  return (
    <div
      className={cn("flex items-center gap-1 overflow-x-auto py-2", className)}
    >
      {/* Start node */}
      <button
        className="flex-shrink-0 flex items-center"
        onClick={() => onStepSelect(null)}
        title="Task Start"
      >
        <div
          className={cn(
            "w-6 h-6 rounded-full flex items-center justify-center transition-colors",
            selectedStepIndex === null
              ? "bg-primary text-primary-foreground"
              : "bg-green-500/20 text-green-600 hover:bg-green-500/30"
          )}
        >
          <CheckCircle className="h-4 w-4" />
        </div>
      </button>

      {/* Step nodes */}
      {steps.map((step, index) => (
        <div key={step.step_id} className="flex items-center">
          {/* Connector line */}
          <div className="w-4 h-0.5 bg-muted" />

          {/* Step node */}
          <button
            className="flex-shrink-0"
            onClick={() => onStepSelect(index)}
            title={`Step ${index + 1}`}
          >
            <div
              className={cn(
                "w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-colors",
                selectedStepIndex === index
                  ? "bg-primary text-primary-foreground"
                  : step.error
                    ? "bg-red-500/20 text-red-600 hover:bg-red-500/30"
                    : "bg-blue-500/20 text-blue-600 hover:bg-blue-500/30"
              )}
            >
              {step.error ? <XCircle className="h-3.5 w-3.5" /> : index + 1}
            </div>
          </button>
        </div>
      ))}

      {/* End node - only show if task is not running */}
      {!isRunning && (
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-muted" />
          <div
            className={cn(
              "w-6 h-6 rounded-full flex items-center justify-center",
              isCompleted && "bg-green-500/20 text-green-600",
              isFailed && "bg-red-500/20 text-red-600",
              isStopped && "bg-gray-500/20 text-gray-600"
            )}
          >
            {isCompleted && <CheckCircle className="h-4 w-4" />}
            {isFailed && <XCircle className="h-4 w-4" />}
            {isStopped && <Square className="h-4 w-4" />}
          </div>
        </div>
      )}

      {/* Running indicator */}
      {isRunning && (
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-muted" />
          <div className="w-6 h-6 rounded-full flex items-center justify-center bg-blue-500/20 text-blue-600">
            <Loader2 className="h-4 w-4 animate-spin" />
          </div>
        </div>
      )}
    </div>
  );
}
