"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { queryClient } from "@/lib/react-query";
import { type ReactNode } from "react";

/**
 * Query Provider Component
 *
 * Wraps the app with TanStack Query's QueryClientProvider.
 * Includes React Query Devtools in development.
 *
 * Usage:
 *   <QueryProvider>
 *     <App />
 *   </QueryProvider>
 */

interface QueryProviderProps {
  children: ReactNode;
}

export function QueryProvider({ children }: QueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === "development" && <ReactQueryDevtools />}
    </QueryClientProvider>
  );
}
