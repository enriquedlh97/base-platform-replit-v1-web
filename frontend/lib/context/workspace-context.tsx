"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import type { WorkspacePublic } from "@/lib/api/generated/types.gen";

/**
 * Workspace Context
 *
 * Provides global workspace state management for the dashboard.
 * Stores the currently selected workspace and provides helpers for switching.
 */

type WorkspaceContextType = {
  currentWorkspace: WorkspacePublic | null;
  setCurrentWorkspace: (workspace: WorkspacePublic | null) => void;
  workspaceId: string | null;
};

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(
  undefined
);

/**
 * WorkspaceProvider
 *
 * Wraps the dashboard layout to provide workspace state to all children.
 */
export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [currentWorkspace, setCurrentWorkspace] =
    useState<WorkspacePublic | null>(null);

  const value: WorkspaceContextType = {
    currentWorkspace,
    setCurrentWorkspace,
    workspaceId: currentWorkspace?.id ?? null,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

/**
 * useWorkspaceContext
 *
 * Hook to access workspace context.
 * Must be used within a WorkspaceProvider.
 */
export function useWorkspaceContext() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error(
      "useWorkspaceContext must be used within WorkspaceProvider"
    );
  }
  return context;
}

/**
 * useCurrentWorkspace
 *
 * Convenience hook to get the current workspace.
 */
export function useCurrentWorkspace() {
  const { currentWorkspace } = useWorkspaceContext();
  return currentWorkspace;
}
