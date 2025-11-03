"use client";

import { SignupForm } from "@/components/signup-form";

/**
 * Signup Page
 *
 * Uses shadcn signup-03 component with integrated Supabase authentication.
 * Supports email/password and social auth (Google, Apple) with Zod validation.
 */
export default function SignupPage() {
  return <SignupForm />;
}
