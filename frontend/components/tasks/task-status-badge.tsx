"use client";

import { Badge } from "@/components/ui/badge";
import {
  Loader2,
  CheckCircle,
  XCircle,
  Square,
  Clock,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface TaskStatusBadgeProps {
  status: string;
  className?: string;
}

export function TaskStatusBadge({ status, className }: TaskStatusBadgeProps) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case "pending":
        return {
          label: "Pending",
          icon: Clock,
          variant: "secondary" as const,
          className: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
        };
      case "running":
        return {
          label: "Running",
          icon: Loader2,
          variant: "secondary" as const,
          className: "bg-blue-500/10 text-blue-600 border-blue-500/20",
          iconAnimate: true,
        };
      case "completed":
        return {
          label: "Completed",
          icon: CheckCircle,
          variant: "default" as const,
          className: "bg-green-500/10 text-green-600 border-green-500/20",
        };
      case "failed":
        return {
          label: "Failed",
          icon: XCircle,
          variant: "destructive" as const,
          className: "bg-red-500/10 text-red-600 border-red-500/20",
        };
      case "stopped":
        return {
          label: "Stopped",
          icon: Square,
          variant: "outline" as const,
          className: "bg-gray-500/10 text-gray-600 border-gray-500/20",
        };
      case "timeout":
        return {
          label: "Timed Out",
          icon: AlertCircle,
          variant: "destructive" as const,
          className: "bg-orange-500/10 text-orange-600 border-orange-500/20",
        };
      default:
        return {
          label: status,
          icon: Clock,
          variant: "outline" as const,
          className: "",
        };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  return (
    <Badge
      variant={config.variant}
      className={cn("gap-1.5 font-medium", config.className, className)}
    >
      <Icon
        className={cn("h-3.5 w-3.5", config.iconAnimate && "animate-spin")}
      />
      {config.label}
    </Badge>
  );
}
