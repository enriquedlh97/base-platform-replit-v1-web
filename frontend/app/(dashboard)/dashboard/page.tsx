"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { useAuthStatus } from "@/lib/auth/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { useWorkspace } from "@/lib/api/hooks/use-workspaces";

/**
 * Dashboard Home Page
 *
 * Shows workspace overview and quick actions.
 * Displays basic stats and navigation to key areas.
 */
export default function DashboardPage() {
  const { user, isLoading: authLoading } = useAuthStatus();
  const { data: workspace, isLoading: workspaceLoading } = useWorkspace();

  if (authLoading || workspaceLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">
          Welcome back, {user?.name || "User"}!
        </h1>
        <p className="text-muted-foreground">
          Here&apos;s an overview of your workspace.
        </p>
      </div>

      {/* Workspace Info Card */}
      {workspace && (
        <Card>
          <CardHeader>
            <CardTitle>Workspace</CardTitle>
            <CardDescription>
              {workspace.name} • {workspace.handle}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">
                  Type
                </p>
                <p className="text-base capitalize">{workspace.type}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">
                  Tone
                </p>
                <p className="text-base capitalize">{workspace.tone}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Get started with common tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <Button
              variant="outline"
              className="h-auto flex-col items-start justify-start p-6"
            >
              <Plus className="mb-2 h-6 w-6" />
              <span className="font-semibold">Add Service</span>
              <span className="text-sm text-muted-foreground">
                Create a new service offering
              </span>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col items-start justify-start p-6"
            >
              <Plus className="mb-2 h-6 w-6" />
              <span className="font-semibold">Add Connector</span>
              <span className="text-sm text-muted-foreground">
                Connect your scheduling platform
              </span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Conversations</CardTitle>
          <CardDescription>Your latest interactions</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No conversations yet.</p>
        </CardContent>
      </Card>
    </div>
  );
}
