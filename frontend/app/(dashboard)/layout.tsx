import { AppSidebar } from "@/components/layout/app-sidebar";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";

/**
 * Dashboard Layout
 *
 * Wraps all dashboard pages with shadcn's responsive SidebarProvider.
 * SidebarProvider automatically handles mobile hamburger menu and desktop sidebar.
 * No custom responsive logic needed - it's all built-in to shadcn's Sidebar component.
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="flex h-full flex-col">
        <header className="flex h-12 items-center gap-2 border-b px-4">
          <SidebarTrigger />
          {/* Mobile menu toggle appears here automatically */}
        </header>
        <div className="flex flex-1 flex-col overflow-auto">
          <main className="flex-1 p-4 md:p-6 lg:p-8">{children}</main>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
