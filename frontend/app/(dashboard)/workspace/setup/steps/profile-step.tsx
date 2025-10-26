"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useSetupWizard } from "@/lib/context/setup-wizard-context";
import {
  profileStepSchema,
  type ProfileStepValues,
} from "@/lib/validation/setup";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

/**
 * Step 1: Profile & Basic Info
 *
 * Collects profile type (Individual/Business), basic information,
 * tone, timezone, and workspace handle.
 */
export function ProfileStep() {
  const { state, updateProfile, nextStep } = useSetupWizard();

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<ProfileStepValues>({
    resolver: zodResolver(profileStepSchema),
    defaultValues: {
      profileType: state.profile.profileType || "individual",
      name: state.profile.name || "",
      avatarUrl: state.profile.avatarUrl || "",
      bio: state.profile.bio || "",
      businessName: state.profile.businessName || "",
      logoUrl: state.profile.logoUrl || "",
      tagline: state.profile.tagline || "",
      tone: state.profile.tone || "professional",
      timezone: state.profile.timezone || "America/Los_Angeles",
      handle: state.profile.handle || "",
    },
  });

  const profileType = watch("profileType");
  const name = watch("name");
  const businessName = watch("businessName");

  // Auto-generate handle from name
  useEffect(() => {
    if (name && !state.profile.handle) {
      const generatedHandle = name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "");
      if (generatedHandle) {
        setValue("handle", generatedHandle);
      }
    } else if (businessName && !state.profile.handle) {
      const generatedHandle = businessName
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "");
      if (generatedHandle) {
        setValue("handle", generatedHandle);
      }
    }
  }, [name, businessName, setValue, state.profile.handle]);

  const onSubmit = (data: ProfileStepValues) => {
    updateProfile(data);
    nextStep();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile & Basic Info</CardTitle>
        <CardDescription>
          Tell us about yourself or your business
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Profile Type */}
          <div className="space-y-3">
            <Label>Profile Type</Label>
            <RadioGroup
              value={profileType}
              onValueChange={(value) =>
                setValue("profileType", value as "individual" | "business")
              }
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="individual" id="individual" />
                <Label htmlFor="individual">Individual</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="business" id="business" />
                <Label htmlFor="business">Business</Label>
              </div>
            </RadioGroup>
            {errors.profileType && (
              <p className="text-sm text-destructive">
                {errors.profileType.message}
              </p>
            )}
          </div>

          {/* Conditional Fields */}
          {profileType === "individual" ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  {...register("name")}
                  placeholder="Your name"
                  aria-invalid={!!errors.name}
                />
                {errors.name && (
                  <p className="text-sm text-destructive">
                    {errors.name.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="avatarUrl">Avatar URL (optional)</Label>
                <Input
                  id="avatarUrl"
                  {...register("avatarUrl")}
                  placeholder="https://example.com/avatar.jpg"
                  aria-invalid={!!errors.avatarUrl}
                />
                {errors.avatarUrl && (
                  <p className="text-sm text-destructive">
                    {errors.avatarUrl.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="bio">Short Bio (optional)</Label>
                <Input
                  id="bio"
                  {...register("bio")}
                  placeholder="A brief description of yourself"
                  aria-invalid={!!errors.bio}
                />
                {errors.bio && (
                  <p className="text-sm text-destructive">
                    {errors.bio.message}
                  </p>
                )}
              </div>
            </>
          ) : (
            <>
              <div className="space-y-2">
                <Label htmlFor="businessName">Business Name</Label>
                <Input
                  id="businessName"
                  {...register("businessName")}
                  placeholder="Your business name"
                  aria-invalid={!!errors.businessName}
                />
                {errors.businessName && (
                  <p className="text-sm text-destructive">
                    {errors.businessName.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="logoUrl">Logo URL (optional)</Label>
                <Input
                  id="logoUrl"
                  {...register("logoUrl")}
                  placeholder="https://example.com/logo.png"
                  aria-invalid={!!errors.logoUrl}
                />
                {errors.logoUrl && (
                  <p className="text-sm text-destructive">
                    {errors.logoUrl.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="tagline">Tagline (optional)</Label>
                <Input
                  id="tagline"
                  {...register("tagline")}
                  placeholder="Your business tagline"
                  aria-invalid={!!errors.tagline}
                />
                {errors.tagline && (
                  <p className="text-sm text-destructive">
                    {errors.tagline.message}
                  </p>
                )}
              </div>
            </>
          )}

          {/* Tone */}
          <div className="space-y-2">
            <Label htmlFor="tone">Tone</Label>
            <Select
              value={watch("tone")}
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
              <p className="text-sm text-destructive">{errors.tone.message}</p>
            )}
          </div>

          {/* Timezone */}
          <div className="space-y-2">
            <Label htmlFor="timezone">Timezone</Label>
            <Select
              value={watch("timezone")}
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

          {/* Handle */}
          <div className="space-y-2">
            <Label htmlFor="handle">Workspace Handle</Label>
            <Input
              id="handle"
              {...register("handle")}
              placeholder="my-workspace"
              aria-invalid={!!errors.handle}
            />
            {errors.handle && (
              <p className="text-sm text-destructive">
                {errors.handle.message}
              </p>
            )}
            <p className="text-sm text-muted-foreground">
              URL-friendly identifier (auto-generated from name)
            </p>
          </div>

          <Button type="submit" className="w-full">
            Continue
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
