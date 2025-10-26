"use client";

import { useState } from "react";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { ServicesSection } from "@/components/settings/services-section";
import {
  workspaceSchema,
  type WorkspaceFormValues,
} from "@/lib/validation/workspace";
import {
  useWorkspace,
  useUpdateWorkspace,
  useDeleteWorkspace,
} from "@/lib/api/hooks/use-workspaces";
import { useWorkspaceConnectors } from "@/lib/api/hooks/use-scheduling-connectors";
import { useUser } from "@/lib/api/hooks/use-users";
import { toast } from "sonner";

/**
 * Workspace Settings Page
 *
 * Comprehensive settings management for:
 * - Workspace details (handle, name, type, tone, timezone)
 * - Services (CRUD with reordering)
 * - Scheduling connectors (Calendly link management)
 * - Profile & FAQs (bio, FAQs, profile type)
 */
export default function SettingsPage() {
  const { data: workspace } = useWorkspace();
  useUser(); // Fetch user data (will be used for profile section)
  const { data: connectors } = useWorkspaceConnectors(workspace?.id || "");
  const updateWorkspace = useUpdateWorkspace(workspace?.id || "");
  const deleteWorkspace = useDeleteWorkspace();
  const [isDeleting, setIsDeleting] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<WorkspaceFormValues>({
    resolver: zodResolver(workspaceSchema),
    defaultValues: workspace
      ? {
          handle: workspace.handle,
          name: workspace.name,
          type: workspace.type,
          tone: workspace.tone,
          timezone: workspace.timezone,
        }
      : undefined,
  });

  const watchedType = watch("type");
  const watchedTone = watch("tone");
  const watchedTimezone = watch("timezone");

  const onSubmit = async (data: WorkspaceFormValues) => {
    if (!workspace) return;

    try {
      await updateWorkspace.mutateAsync(data);
      toast.success("Workspace updated successfully!");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to update workspace"
      );
    }
  };

  const handleDelete = async () => {
    if (!workspace) return;

    setIsDeleting(true);
    try {
      await deleteWorkspace.mutateAsync(workspace.id);
      toast.success("Workspace deleted successfully!");
      setIsDeleteDialogOpen(false);
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to delete workspace"
      );
      setIsDeleting(false);
    }
  };

  if (!workspace) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-sm text-muted-foreground">No workspace found.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your workspace settings</p>
      </div>

      {/* Edit Workspace Form */}
      <Card>
        <CardHeader>
          <CardTitle>Workspace Details</CardTitle>
          <CardDescription>Update your workspace information</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Handle */}
            <div className="space-y-2">
              <Label htmlFor="handle">Workspace Handle</Label>
              <Input
                id="handle"
                {...register("handle")}
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
                {...register("name")}
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
              <Label htmlFor="type">Profile Type</Label>
              <Select
                value={watchedType}
                onValueChange={(value) => setValue("type", value)}
              >
                <SelectTrigger aria-invalid={!!errors.type}>
                  <SelectValue placeholder="Select a type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="individual">Individual</SelectItem>
                  <SelectItem value="business">Business</SelectItem>
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
              >
                <SelectTrigger aria-invalid={!!errors.tone}>
                  <SelectValue placeholder="Select a tone" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="professional">Professional</SelectItem>
                  <SelectItem value="warm">Warm</SelectItem>
                  <SelectItem value="pragmatic">Pragmatic</SelectItem>
                  <SelectItem value="executive">Executive-friendly</SelectItem>
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

            <Button type="submit" disabled={updateWorkspace.isPending}>
              {updateWorkspace.isPending ? "Saving..." : "Save Changes"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Services Section */}
      <ServicesSection workspaceId={workspace.id} />

      {/* Connectors Section - Placeholder for now */}
      <Card>
        <CardHeader>
          <CardTitle>Scheduling Connectors</CardTitle>
          <CardDescription>Connect your scheduling platform</CardDescription>
        </CardHeader>
        <CardContent>
          {connectors && connectors.length > 0 ? (
            <div className="space-y-2">
              {connectors.map((connector) => {
                const link =
                  connector.config &&
                  typeof connector.config === "object" &&
                  "link" in connector.config &&
                  typeof connector.config.link === "string"
                    ? connector.config.link
                    : null;

                return (
                  <div
                    key={connector.id}
                    className="flex items-center justify-between rounded-lg border p-3"
                  >
                    <div>
                      <p className="font-medium capitalize">{connector.type}</p>
                      {link && (
                        <p className="text-sm text-muted-foreground">{link}</p>
                      )}
                    </div>
                    <Badge
                      variant={connector.is_active ? "default" : "secondary"}
                    >
                      {connector.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No connectors yet</p>
          )}
        </CardContent>
      </Card>

      {/* Delete Workspace */}
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Danger Zone</CardTitle>
          <CardDescription>Permanently delete your workspace</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="mb-4 text-sm text-muted-foreground">
            Once you delete a workspace, there is no going back. Please be
            certain.
          </p>
          <Dialog
            open={isDeleteDialogOpen}
            onOpenChange={setIsDeleteDialogOpen}
          >
            <DialogTrigger asChild>
              <Button variant="destructive">Delete Workspace</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Are you absolutely sure?</DialogTitle>
                <DialogDescription>
                  This action cannot be undone. This will permanently delete
                  your workspace and all associated data.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsDeleteDialogOpen(false)}
                  disabled={isDeleting}
                >
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                  disabled={isDeleting}
                >
                  {isDeleting ? "Deleting..." : "Delete"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardContent>
      </Card>
    </div>
  );
}
