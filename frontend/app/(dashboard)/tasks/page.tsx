"use client";

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

export default function TasksPage() {
  // CUA frontend URL - in production, this should come from env vars
  const cuaUrl = process.env.NEXT_PUBLIC_CUA_URL || "http://localhost:7860";

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
              <div className="flex flex-col gap-2">
                <h1 className="text-3xl font-bold tracking-tight">Tasks</h1>
                <p className="text-muted-foreground">
                  View and monitor active Computer Use Agent tasks. Tasks are
                  automatically created when appointments are scheduled.
                </p>
              </div>

              <Card className="flex-1">
                <CardHeader>
                  <CardTitle>Active Tasks</CardTitle>
                  <CardDescription>
                    Live view of Computer Use Agent task execution. This shows
                    real-time screenshots and steps as tasks are processed.
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  <div
                    className="relative w-full"
                    style={{
                      height: "calc(100vh - 300px)",
                      minHeight: "600px",
                    }}
                  >
                    <iframe
                      src={`${cuaUrl}/task`}
                      className="absolute inset-0 w-full h-full border-0"
                      title="CUA Task Viewer"
                      allow="clipboard-read; clipboard-write"
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
