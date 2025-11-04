"use client";

import { AppSidebar } from "@/components/app-sidebar";
import { KnowledgeBaseEditor } from "@/components/knowledge-base-editor";
import { SiteHeader } from "@/components/site-header";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { useWorkspace } from "@/lib/api/hooks/use-workspaces";
import { Skeleton } from "@/components/ui/skeleton";

export default function KnowledgeBasePage() {
  const { data: workspace, isLoading, error } = useWorkspace();

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
              {isLoading && (
                <div className="flex flex-col gap-4">
                  <Skeleton className="h-8 w-64" />
                  <Skeleton className="h-4 w-96" />
                  <Skeleton className="h-[400px] w-full" />
                </div>
              )}
              {error && (
                <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-sm text-destructive">
                  Failed to load workspace. Please try refreshing the page.
                </div>
              )}
              {workspace && !isLoading && (
                <KnowledgeBaseEditor
                  workspaceId={workspace.id}
                  initialContent={workspace.knowledge_base}
                />
              )}
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
