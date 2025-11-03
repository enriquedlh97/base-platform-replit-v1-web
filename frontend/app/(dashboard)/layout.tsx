/**
 * Dashboard Layout
 *
 * Passes through children. The dashboard page handles its own layout
 * with SidebarProvider and sidebar components.
 */
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
