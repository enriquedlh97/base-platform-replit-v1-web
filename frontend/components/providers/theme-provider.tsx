"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";
import type { ComponentProps } from "react";

/**
 * Theme Provider Component
 *
 * Wraps the app with next-themes ThemeProvider for dark/light mode support.
 * Follows system preference by default.
 *
 * Usage:
 *   <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
 *     <App />
 *   </ThemeProvider>
 */

interface ThemeProviderProps extends ComponentProps<typeof NextThemesProvider> {
  children: React.ReactNode;
}

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
