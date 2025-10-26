import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

/**
 * Home Page / Landing Page
 *
 * Public landing page that redirects authenticated users to dashboard.
 * Shows marketing content for unauthenticated users.
 */
export default async function HomePage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  // Redirect authenticated users to dashboard
  if (session) {
    redirect("/dashboard");
  }

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold">Scheduling Platform</h1>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" asChild>
              <Link href="/login">Sign In</Link>
            </Button>
            <Button asChild>
              <Link href="/signup">Get Started</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <div className="container mx-auto px-4 py-24">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
              AI-Powered Scheduling for Modern Teams
            </h1>
            <p className="mt-6 text-lg leading-8 text-muted-foreground">
              Build intelligent scheduling agents that answer questions and book
              meetings automatically. Perfect for freelancers, consultants, and
              agencies.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Button size="lg" asChild>
                <Link href="/signup">Get Started</Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link href="/login">Sign In</Link>
              </Button>
            </div>
          </div>

          {/* Features Grid */}
          <div className="mt-24 grid gap-8 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>AI Agents</CardTitle>
                <CardDescription>
                  Intelligent agents that answer questions and schedule meetings
                  automatically
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Calendly Integration</CardTitle>
                <CardDescription>
                  Seamlessly connect with Calendly for meeting scheduling
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Multiple Workspaces</CardTitle>
                <CardDescription>
                  Manage multiple client workspaces from one dashboard
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t">
        <div className="container mx-auto px-4 py-12">
          <div className="text-center text-sm text-muted-foreground">
            <p>© 2024 Scheduling Platform. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
