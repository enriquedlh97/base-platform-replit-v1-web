"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  MousePointer,
  Keyboard,
  ArrowLeft,
  MessageSquare,
  Clock,
  Target,
} from "lucide-react";

interface TaskAction {
  function_name: string;
  parameters: Record<string, unknown>;
  description?: string;
}

interface TaskStep {
  step_id: string;
  image?: string;
  thought?: string;
  actions?: TaskAction[];
  error?: string;
  duration?: number;
  input_tokens_used?: number;
  output_tokens_used?: number;
}

interface TaskStepCardProps {
  step: TaskStep;
  stepNumber: number;
  isSelected?: boolean;
  onClick?: () => void;
  className?: string;
}

function ActionIcon({ actionName }: { actionName: string }) {
  switch (actionName) {
    case "click":
    case "double_click":
    case "right_click":
      return <MousePointer className="h-3 w-3" />;
    case "write":
    case "press":
      return <Keyboard className="h-3 w-3" />;
    case "go_back":
      return <ArrowLeft className="h-3 w-3" />;
    case "final_answer":
      return <MessageSquare className="h-3 w-3" />;
    case "wait":
      return <Clock className="h-3 w-3" />;
    default:
      return <Target className="h-3 w-3" />;
  }
}

function formatActionDescription(action: TaskAction): string {
  if (action.description) return action.description;

  const { function_name, parameters } = action;
  switch (function_name) {
    case "click":
      return `Click at (${parameters.x || parameters.arg_0}, ${parameters.y || parameters.arg_1})`;
    case "write":
      return `Type: "${(parameters.text || parameters.arg_0 || "").toString().slice(0, 50)}..."`;
    case "press":
      return `Press: ${parameters.key || parameters.arg_0}`;
    case "final_answer":
      return `Final answer: ${(parameters.answer || parameters.arg_0 || "").toString().slice(0, 50)}...`;
    case "scroll":
      return `Scroll ${parameters.direction || parameters.arg_2}`;
    case "wait":
      return `Wait ${parameters.seconds || parameters.arg_0}s`;
    default:
      return function_name;
  }
}

export function TaskStepCard({
  step,
  stepNumber,
  isSelected,
  onClick,
  className,
}: TaskStepCardProps) {
  const primaryAction = step.actions?.[0];

  return (
    <Card
      className={cn(
        "cursor-pointer transition-all hover:shadow-md",
        isSelected && "ring-2 ring-primary",
        className
      )}
      onClick={onClick}
    >
      <CardContent className="p-3">
        <div className="flex items-start gap-3">
          {/* Step thumbnail */}
          {step.image && (
            <div className="relative w-16 h-12 rounded overflow-hidden bg-muted flex-shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={step.image}
                alt={`Step ${stepNumber}`}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          {/* Step info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="outline" className="text-xs">
                Step {stepNumber}
              </Badge>
              {primaryAction && (
                <Badge variant="secondary" className="text-xs gap-1">
                  <ActionIcon actionName={primaryAction.function_name} />
                  {primaryAction.function_name}
                </Badge>
              )}
            </div>

            {/* Thought preview */}
            {step.thought && (
              <p className="text-xs text-muted-foreground line-clamp-2">
                {step.thought}
              </p>
            )}

            {/* Action description */}
            {primaryAction && (
              <p className="text-xs text-foreground/80 mt-1">
                {formatActionDescription(primaryAction)}
              </p>
            )}

            {/* Error */}
            {step.error && (
              <p className="text-xs text-red-500 mt-1 line-clamp-1">
                Error: {step.error}
              </p>
            )}

            {/* Timing info */}
            {step.duration !== undefined && step.duration > 0 && (
              <p className="text-xs text-muted-foreground mt-1">
                {step.duration.toFixed(1)}s
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export type { TaskStep, TaskAction };
