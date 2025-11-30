"use client";

import { useState } from "react";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ConversationCard } from "@/components/conversations/conversation-card";
import { useConversations } from "@/lib/api/hooks/use-conversations";
import { useWorkspace } from "@/lib/api/hooks/use-workspaces";
import { RefreshCw, Inbox, MessageSquare } from "lucide-react";
import type { ConversationSummary } from "@/lib/api/hooks/use-conversations";

type TabValue = "all" | "active" | "closed";

export default function ConversationsPage() {
  const [activeTab, setActiveTab] = useState<TabValue>("all");
  const { data: workspace, isLoading: isLoadingWorkspace } = useWorkspace();

  // Fetch conversations
  const {
    data: conversations,
    isLoading: isLoadingConversations,
    refetch,
    isFetching,
  } = useConversations(workspace?.id, { limit: 100 });

  // Filter conversations by status
  const allConversations = conversations?.data ?? [];
  const activeConversations = allConversations.filter(
    (c: ConversationSummary) => c.status === "active"
  );
  const closedConversations = allConversations.filter(
    (c: ConversationSummary) => c.status === "closed" || c.status === "resolved"
  );

  const isLoading = isLoadingWorkspace || isLoadingConversations;

  const renderConversationList = (
    convos: ConversationSummary[] | undefined
  ) => {
    if (!convos || convos.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Inbox className="h-12 w-12 text-muted-foreground/50 mb-4" />
          <h3 className="text-lg font-medium text-muted-foreground">
            No conversations found
          </h3>
          <p className="text-sm text-muted-foreground/70 mt-1">
            Conversations will appear here when visitors chat with your AI
            assistant.
          </p>
        </div>
      );
    }

    return (
      <div className="grid gap-4">
        {convos.map((conversation) => (
          <ConversationCard key={conversation.id} conversation={conversation} />
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
                <Skeleton className="h-5 w-1/3" />
                <Skeleton className="h-4 w-1/2" />
              </div>
              <Skeleton className="h-6 w-16" />
            </div>
          </CardHeader>
          <CardContent className="pt-0 space-y-3">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-4 w-3/4" />
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
                  <h1 className="text-3xl font-bold tracking-tight">
                    Conversations
                  </h1>
                  <p className="text-muted-foreground">
                    View and manage conversations from your public chat.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refetch()}
                  disabled={isFetching}
                >
                  <RefreshCw
                    className={`h-4 w-4 mr-2 ${isFetching ? "animate-spin" : ""}`}
                  />
                  Refresh
                </Button>
              </div>

              {/* Summary stats */}
              {!isLoading && conversations && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <Card className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <MessageSquare className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <p className="text-2xl font-bold">
                          {conversations.count}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Total Conversations
                        </p>
                      </div>
                    </div>
                  </Card>
                  <Card className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                        <MessageSquare className="h-5 w-5 text-green-600" />
                      </div>
                      <div>
                        <p className="text-2xl font-bold">
                          {activeConversations.length}
                        </p>
                        <p className="text-xs text-muted-foreground">Active</p>
                      </div>
                    </div>
                  </Card>
                  <Card className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg bg-gray-500/10 flex items-center justify-center">
                        <MessageSquare className="h-5 w-5 text-gray-600" />
                      </div>
                      <div>
                        <p className="text-2xl font-bold">
                          {closedConversations.length}
                        </p>
                        <p className="text-xs text-muted-foreground">Closed</p>
                      </div>
                    </div>
                  </Card>
                </div>
              )}

              {/* Tabs */}
              <Tabs
                value={activeTab}
                onValueChange={(v) => setActiveTab(v as TabValue)}
              >
                <TabsList>
                  <TabsTrigger value="all" className="gap-2">
                    All
                    {conversations?.count !== undefined &&
                      conversations.count > 0 && (
                        <span className="ml-1 rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
                          {conversations.count}
                        </span>
                      )}
                  </TabsTrigger>
                  <TabsTrigger value="active" className="gap-2">
                    Active
                    {activeConversations.length > 0 && (
                      <span className="ml-1 rounded-full bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-600">
                        {activeConversations.length}
                      </span>
                    )}
                  </TabsTrigger>
                  <TabsTrigger value="closed" className="gap-2">
                    Closed
                    {closedConversations.length > 0 && (
                      <span className="ml-1 rounded-full bg-gray-500/10 px-2 py-0.5 text-xs font-medium text-gray-600">
                        {closedConversations.length}
                      </span>
                    )}
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="all" className="mt-6">
                  {isLoading
                    ? renderSkeletons()
                    : renderConversationList(allConversations)}
                </TabsContent>

                <TabsContent value="active" className="mt-6">
                  {isLoading
                    ? renderSkeletons()
                    : renderConversationList(activeConversations)}
                </TabsContent>

                <TabsContent value="closed" className="mt-6">
                  {isLoading
                    ? renderSkeletons()
                    : renderConversationList(closedConversations)}
                </TabsContent>
              </Tabs>
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
