"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { LoginForm } from "@/components/login-form";

/**
 * Login Page
 *
 * Uses shadcn login-03 component with integrated Supabase authentication.
 * Supports email/password and social auth (Google, Apple) with Zod validation.
 */
function LoginPageContent() {
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/knowledge-base";

  const handleSuccess = () => {
    // Force a hard navigation to ensure session is picked up
    window.location.href = redirectTo;
  };

  return <LoginForm redirectTo={redirectTo} onSuccess={handleSuccess} />;
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginForm redirectTo="/knowledge-base" />}>
      <LoginPageContent />
    </Suspense>
  );
}
