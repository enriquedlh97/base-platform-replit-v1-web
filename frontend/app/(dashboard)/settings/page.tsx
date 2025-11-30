"use client";

import { useState, useRef, useEffect } from "react";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import {
  useWorkspace,
  useUpdateWorkspace,
  useUploadWorkspaceProfileImage,
} from "@/lib/api/hooks/use-workspaces";
import { useUser } from "@/lib/api/hooks/use-users";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { toast } from "sonner";
import { Upload, Loader2 } from "lucide-react";

export default function SettingsPage() {
  const {
    data: workspace,
    isLoading: workspaceLoading,
    error: workspaceError,
  } = useWorkspace();
  const { data: user, isLoading: userLoading } = useUser();
  const updateWorkspace = useUpdateWorkspace(workspace?.id || "");
  const uploadProfileImage = useUploadWorkspaceProfileImage(
    workspace?.id || ""
  );

  // Derive initial values from workspace/user data
  const initialPublicName = workspace?.public_name || user?.full_name || "";
  const initialSubtitle = workspace?.subtitle || "";
  const initialDescription = workspace?.description || "";
  const initialProfileImagePreview = workspace?.profile_image_url || null;

  const [publicName, setPublicName] = useState(initialPublicName);
  const [subtitle, setSubtitle] = useState(initialSubtitle);
  const [description, setDescription] = useState(initialDescription);
  const [profileImagePreview, setProfileImagePreview] = useState<string | null>(
    initialProfileImagePreview
  );
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Update form when workspace or user changes (only if values actually changed)
  useEffect(() => {
    if (workspace) {
      const newPublicName = workspace.public_name || user?.full_name || "";
      const newSubtitle = workspace.subtitle || "";
      const newDescription = workspace.description || "";
      const newProfileImagePreview = workspace.profile_image_url || null;

      if (newPublicName !== publicName) setPublicName(newPublicName);
      if (newSubtitle !== subtitle) setSubtitle(newSubtitle);
      if (newDescription !== description) setDescription(newDescription);
      if (newProfileImagePreview !== profileImagePreview)
        setProfileImagePreview(newProfileImagePreview);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspace, user]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith("image/")) {
        toast.error("Please select an image file");
        return;
      }
      // Validate file size (5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error("Image must be less than 5MB");
        return;
      }
      // Store selected file
      setSelectedFile(file);
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setProfileImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUploadImage = async () => {
    if (!selectedFile || !workspace) return;

    try {
      await uploadProfileImage.mutateAsync(selectedFile);
      toast.success("Profile image uploaded successfully!");
      setSelectedFile(null);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to upload image"
      );
    }
  };

  const handleSave = async () => {
    if (!workspace) return;

    try {
      await updateWorkspace.mutateAsync({
        public_name: publicName || null,
        subtitle: subtitle || null,
        description: description || null,
      });
      toast.success("Settings saved successfully!");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to save settings"
      );
    }
  };

  const isLoading = workspaceLoading || userLoading;
  const isSaving = updateWorkspace.isPending || uploadProfileImage.isPending;

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar variant="inset" />
      <SidebarInset>
        <SiteHeader />
        <div className="flex flex-1 flex-col">
          <div className="@container/main flex flex-1 flex-col gap-2">
            <div className="flex flex-col gap-4 py-4 px-4 md:gap-6 md:py-6 lg:px-6">
              {isLoading && (
                <div className="flex flex-col gap-4">
                  <Skeleton className="h-8 w-64" />
                  <Skeleton className="h-4 w-96" />
                  <Skeleton className="h-[400px] w-full" />
                </div>
              )}
              {workspaceError && (
                <div className="rounded-lg border border-destructive bg-destructive/10 p-4 text-sm text-destructive">
                  Failed to load workspace. Please try refreshing the page.
                </div>
              )}
              {workspace && !isLoading && (
                <Card>
                  <CardHeader>
                    <CardTitle>Public Profile Settings</CardTitle>
                    <CardDescription>
                      Configure how your profile appears on the public chat page
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Profile Image Upload */}
                    <div className="space-y-2">
                      <Label>Profile Image</Label>
                      <div className="flex items-center gap-4">
                        <Avatar className="h-20 w-20">
                          <AvatarImage
                            src={profileImagePreview || undefined}
                            alt="Profile"
                          />
                          <AvatarFallback>
                            {publicName
                              ? publicName
                                  .split(" ")
                                  .map((n) => n[0])
                                  .join("")
                                  .toUpperCase()
                                  .slice(0, 2)
                              : "U"}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col gap-2">
                          <Input
                            ref={fileInputRef}
                            type="file"
                            accept="image/jpeg,image/png,image/webp"
                            onChange={handleFileSelect}
                            className="hidden"
                          />
                          <Button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            size="sm"
                            variant="outline"
                            className="w-64 cursor-pointer hover:bg-accent hover:text-accent-foreground transition-colors"
                          >
                            Choose File
                          </Button>
                          <Button
                            onClick={handleUploadImage}
                            disabled={
                              !selectedFile || uploadProfileImage.isPending
                            }
                            size="sm"
                            variant="outline"
                          >
                            {uploadProfileImage.isPending ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Uploading...
                              </>
                            ) : (
                              <>
                                <Upload className="mr-2 h-4 w-4" />
                                Upload Image
                              </>
                            )}
                          </Button>
                          <p className="text-xs text-muted-foreground">
                            Max size: 5MB. Allowed: JPEG, PNG, WebP
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Public Name */}
                    <div className="space-y-2">
                      <Label htmlFor="public-name">Public Name</Label>
                      <Input
                        id="public-name"
                        value={publicName}
                        onChange={(e) => setPublicName(e.target.value)}
                        placeholder={user?.full_name || "Your name"}
                        maxLength={255}
                      />
                      <p className="text-xs text-muted-foreground">
                        This name will be displayed on your public chat page.
                        Defaults to your full name.
                      </p>
                    </div>

                    {/* Subtitle */}
                    <div className="space-y-2">
                      <Label htmlFor="subtitle">Subtitle (Optional)</Label>
                      <Input
                        id="subtitle"
                        value={subtitle}
                        onChange={(e) => setSubtitle(e.target.value)}
                        placeholder="e.g., MIT Sloan MBAn Candidate"
                        maxLength={255}
                      />
                      <p className="text-xs text-muted-foreground">
                        A short subtitle that appears below your name
                      </p>
                    </div>

                    {/* Description */}
                    <div className="space-y-2">
                      <Label htmlFor="description">
                        Description (Optional)
                      </Label>
                      <Textarea
                        id="description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="A brief description about yourself or your business..."
                        rows={4}
                        className="resize-none"
                      />
                      <p className="text-xs text-muted-foreground">
                        A longer description that appears on your public profile
                      </p>
                    </div>

                    {/* Save Button */}
                    <div className="flex justify-end">
                      <Button onClick={handleSave} disabled={isSaving}>
                        {isSaving ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Saving...
                          </>
                        ) : (
                          "Save Changes"
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
