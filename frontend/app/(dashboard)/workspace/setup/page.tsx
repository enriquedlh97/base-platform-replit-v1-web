"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateWorkspace } from "@/lib/api/hooks/use-workspaces";
import {
  workspaceSchema,
  type WorkspaceFormValues,
} from "@/lib/validation/workspace";
import { toast } from "sonner";

/**
 * Workspace Setup Page
 *
 * First-time workspace creation form for new users.
 * Includes all required fields: handle, name, type, tone, timezone.
 */
export default function WorkspaceSetupPage() {
  const router = useRouter();
  const createWorkspace = useCreateWorkspace();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<WorkspaceFormValues>({
    resolver: zodResolver(workspaceSchema),
  });

  const watchedType = watch("type");
  const watchedTone = watch("tone");
  const watchedTimezone = watch("timezone");

  const onSubmit = async (data: WorkspaceFormValues) => {
    setIsLoading(true);

    try {
      await createWorkspace.mutateAsync(data);
      toast.success("Workspace created successfully!");
      router.push("/dashboard");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to create workspace"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Create Your Workspace</CardTitle>
          <CardDescription>
            Set up your workspace to get started
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Handle */}
            <div className="space-y-2">
              <Label htmlFor="handle">Workspace Handle</Label>
              <Input
                id="handle"
                placeholder="my-workspace"
                {...register("handle")}
                disabled={isLoading}
                aria-invalid={!!errors.handle}
              />
              {errors.handle && (
                <p className="text-sm text-destructive">
                  {errors.handle.message}
                </p>
              )}
              <p className="text-sm text-muted-foreground">
                URL-friendly identifier (lowercase, hyphens allowed)
              </p>
            </div>

            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name">Workspace Name</Label>
              <Input
                id="name"
                placeholder="My Workspace"
                {...register("name")}
                disabled={isLoading}
                aria-invalid={!!errors.name}
              />
              {errors.name && (
                <p className="text-sm text-destructive">
                  {errors.name.message}
                </p>
              )}
            </div>

            {/* Type */}
            <div className="space-y-2">
              <Label htmlFor="type">Workspace Type</Label>
              <Select
                value={watchedType}
                onValueChange={(value) => setValue("type", value)}
                disabled={isLoading}
              >
                <SelectTrigger aria-invalid={!!errors.type}>
                  <SelectValue placeholder="Select a type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="consulting">Consulting</SelectItem>
                  <SelectItem value="agency">Agency</SelectItem>
                  <SelectItem value="freelance">Freelance</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
              {errors.type && (
                <p className="text-sm text-destructive">
                  {errors.type.message}
                </p>
              )}
            </div>

            {/* Tone */}
            <div className="space-y-2">
              <Label htmlFor="tone">Tone</Label>
              <Select
                value={watchedTone}
                onValueChange={(value) => setValue("tone", value)}
                disabled={isLoading}
              >
                <SelectTrigger aria-invalid={!!errors.tone}>
                  <SelectValue placeholder="Select a tone" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="professional">Professional</SelectItem>
                  <SelectItem value="friendly">Friendly</SelectItem>
                  <SelectItem value="casual">Casual</SelectItem>
                  <SelectItem value="formal">Formal</SelectItem>
                </SelectContent>
              </Select>
              {errors.tone && (
                <p className="text-sm text-destructive">
                  {errors.tone.message}
                </p>
              )}
            </div>

            {/* Timezone */}
            <div className="space-y-2">
              <Label htmlFor="timezone">Timezone</Label>
              <Select
                value={watchedTimezone}
                onValueChange={(value) => setValue("timezone", value)}
                disabled={isLoading}
              >
                <SelectTrigger aria-invalid={!!errors.timezone}>
                  <SelectValue placeholder="Select a timezone" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="UTC">UTC</SelectItem>
                  <SelectItem value="America/New_York">Eastern Time</SelectItem>
                  <SelectItem value="America/Chicago">Central Time</SelectItem>
                  <SelectItem value="America/Denver">Mountain Time</SelectItem>
                  <SelectItem value="America/Los_Angeles">
                    Pacific Time
                  </SelectItem>
                  <SelectItem value="Europe/London">London</SelectItem>
                  <SelectItem value="Europe/Paris">Paris</SelectItem>
                </SelectContent>
              </Select>
              {errors.timezone && (
                <p className="text-sm text-destructive">
                  {errors.timezone.message}
                </p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Creating workspace..." : "Create Workspace"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
