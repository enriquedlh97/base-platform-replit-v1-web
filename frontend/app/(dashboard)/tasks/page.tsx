"use client";

import { useState } from "react";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { TaskCard } from "@/components/tasks/task-card";
import { TaskStatusBadge } from "@/components/tasks/task-status-badge";
import {
  useCuaTasks,
  useActiveCuaTasks,
  type CuaTaskSummary,
} from "@/lib/api/hooks/use-cua-tasks";
import { RefreshCw, Inbox } from "lucide-react";

type TabValue = "active" | "all" | "completed" | "failed";

export default function TasksPage() {
  const [activeTab, setActiveTab] = useState<TabValue>("active");

  // Fetch active tasks with polling
  const {
    data: activeTasks,
    isLoading: isLoadingActive,
    refetch: refetchActive,
    isFetching: isFetchingActive,
  } = useActiveCuaTasks({ refetchInterval: 5000 });

  // Fetch all tasks
  const {
    data: allTasks,
    isLoading: isLoadingAll,
    refetch: refetchAll,
    isFetching: isFetchingAll,
  } = useCuaTasks({ limit: 100 });

  // Derive completed and failed tasks from all tasks
  const completedTasks =
    allTasks?.data.filter(
      (task: CuaTaskSummary) =>
        task.status === "completed" || task.status === "stopped"
    ) ?? [];
  const failedTasks =
    allTasks?.data.filter(
      (task: CuaTaskSummary) =>
        task.status === "failed" || task.status === "timeout"
    ) ?? [];

  const handleRefresh = () => {
    if (activeTab === "active") {
      refetchActive();
    } else {
      refetchAll();
    }
  };

  const isFetching = activeTab === "active" ? isFetchingActive : isFetchingAll;

  const renderTaskList = (tasks: CuaTaskSummary[] | undefined) => {
    if (!tasks || tasks.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Inbox className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium text-muted-foreground">
            No tasks found
          </h3>
          <p className="text-sm text-muted-foreground/70 mt-1">
            Tasks will appear here when appointments are scheduled.
          </p>
        </div>
      );
    }

    return (
      <div className="grid gap-4">
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} />
        ))}
      </div>
    );
  };

  const renderSkeletons = () => (
    <div className="grid gap-4">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 space-y-2">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </div>
              <Skeleton className="h-6 w-20" />
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <Skeleton className="h-4 w-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  );

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
          <div className="@container/main flex flex-1 flex-col gap-2">
            <div className="flex flex-col gap-4 py-4 px-4 md:gap-6 md:py-6 lg:px-6">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex flex-col gap-2">
                  <h1 className="text-3xl font-bold tracking-tight">Tasks</h1>
                  <p className="text-muted-foreground">
                    View and monitor Computer Use Agent tasks. Tasks are
                    automatically created when appointments are scheduled.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={isFetching}
                >
                  <RefreshCw
                    className={`h-4 w-4 mr-2 ${
                      isFetching ? "animate-spin" : ""
                    }`}
                  />
                  Refresh
                </Button>
              </div>

              {/* Active tasks summary */}
              {!isLoadingActive && activeTasks && activeTasks.count > 0 && (
                <Card className="border-blue-500/20 bg-blue-500/5">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base font-medium flex items-center gap-2">
                        <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
                        {activeTasks.count} Active Task
                        {activeTasks.count > 1 ? "s" : ""}
                      </CardTitle>
                      <TaskStatusBadge status="running" />
                    </div>
                    <CardDescription>
                      Tasks currently being executed by the Computer Use Agent.
                    </CardDescription>
                  </CardHeader>
                </Card>
              )}

              {/* Tabs */}
              <Tabs
                value={activeTab}
                onValueChange={(v) => setActiveTab(v as TabValue)}
              >
                <TabsList>
                  <TabsTrigger value="active" className="gap-2">
                    Active
                    {activeTasks?.count !== undefined &&
                      activeTasks.count > 0 && (
                        <span className="ml-1 rounded-full bg-blue-500/10 px-2 py-0.5 text-xs font-medium text-blue-600">
                          {activeTasks.count}
                        </span>
                      )}
                  </TabsTrigger>
                  <TabsTrigger value="all" className="gap-2">
                    All
                    {allTasks?.count !== undefined && allTasks.count > 0 && (
                      <span className="ml-1 rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
                        {allTasks.count}
                      </span>
                    )}
                  </TabsTrigger>
                  <TabsTrigger value="completed" className="gap-2">
                    Completed
                    {completedTasks.length > 0 && (
                      <span className="ml-1 rounded-full bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-600">
                        {completedTasks.length}
                      </span>
                    )}
                  </TabsTrigger>
                  <TabsTrigger value="failed" className="gap-2">
                    Failed
                    {failedTasks.length > 0 && (
                      <span className="ml-1 rounded-full bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-600">
                        {failedTasks.length}
                      </span>
                    )}
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="active" className="mt-6">
                  {isLoadingActive
                    ? renderSkeletons()
                    : renderTaskList(activeTasks?.data)}
                </TabsContent>

                <TabsContent value="all" className="mt-6">
                  {isLoadingAll
                    ? renderSkeletons()
                    : renderTaskList(allTasks?.data)}
                </TabsContent>

                <TabsContent value="completed" className="mt-6">
                  {isLoadingAll
                    ? renderSkeletons()
                    : renderTaskList(completedTasks)}
                </TabsContent>

                <TabsContent value="failed" className="mt-6">
                  {isLoadingAll
                    ? renderSkeletons()
                    : renderTaskList(failedTasks)}
                </TabsContent>
              </Tabs>
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
