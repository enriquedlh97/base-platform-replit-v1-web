import { type ReactNode } from "react";

/**
 * Auth Layout
 *
 * Provides a centered card layout for authentication pages (login, signup).
 * Mobile-first responsive design with proper padding and max-width.
 */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">{children}</div>
    </div>
  );
}
