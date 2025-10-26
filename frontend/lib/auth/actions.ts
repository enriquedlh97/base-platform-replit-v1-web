"use server";

import { createClient } from "@/lib/supabase/server";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { cookies } from "next/headers";

/**
 * Server Actions for Authentication
 *
 * These are server-only functions that handle authentication flows.
 * They can be called directly from Server Components or via Client Components.
 */

/**
 * Sign in with email and password
 *
 * Authenticates the user with Supabase and sets up session cookies.
 *
 * @param email - User's email address
 * @param password - User's password
 * @returns Object with success status and optional error message
 */
export async function signIn(email: string, password: string) {
  const supabase = await createClient();
  const cookieStore = await cookies();

  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    return { error: error.message };
  }

  if (data.session) {
    // Set session cookies for middleware
    cookieStore.set("sb-access-token", data.session.access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
    });
    cookieStore.set("sb-refresh-token", data.session.refresh_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
    });
  }

  revalidatePath("/");
  return { success: true };
}

/**
 * Sign up with email and password
 *
 * Creates a new user account with Supabase.
 *
 * @param email - User's email address
 * @param password - User's password
 * @param fullName - User's full name (optional)
 * @returns Object with success status and optional error message
 */
export async function signUp(
  email: string,
  password: string,
  fullName?: string
) {
  const supabase = await createClient();

  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        full_name: fullName,
      },
    },
  });

  if (error) {
    return { error: error.message };
  }

  return { success: true, user: data.user };
}

/**
 * Sign out the current user
 *
 * Clears the Supabase session and removes auth cookies.
 */
export async function signOut() {
  const supabase = await createClient();
  const cookieStore = await cookies();

  await supabase.auth.signOut();

  // Clear auth cookies
  cookieStore.delete("sb-access-token");
  cookieStore.delete("sb-refresh-token");

  revalidatePath("/");
  redirect("/login");
}
