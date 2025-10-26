import { z } from "zod";

/**
 * Setup Wizard Validation Schemas
 *
 * Zod schemas for validating the multi-step setup wizard.
 * Each step has its own schema and they're combined for final submission.
 */

/**
 * Service validation schema
 */
const serviceSchema = z.object({
  name: z.string().min(1, "Service name is required"),
  description: z.string().optional(),
  duration_minutes: z.number().optional(),
  starting_price: z.number().optional(),
});

/**
 * Step 1: Profile & Basic Info Schema
 */
export const profileStepSchema = z.object({
  profileType: z.enum(["individual", "business"]),
  name: z.string().min(1, "Name is required"),
  avatarUrl: z.string().url().optional().or(z.literal("")),
  bio: z.string().optional(),
  businessName: z.string().optional(),
  logoUrl: z.string().url().optional().or(z.literal("")),
  tagline: z.string().optional(),
  tone: z.string().min(1, "Tone is required"),
  timezone: z.string().min(1, "Timezone is required"),
  handle: z
    .string()
    .min(3, "Handle must be at least 3 characters")
    .max(100, "Handle must be less than 100 characters")
    .regex(
      /^[a-z0-9-]+$/,
      "Handle can only contain lowercase letters, numbers, and hyphens"
    ),
});

export type ProfileStepValues = z.infer<typeof profileStepSchema>;

/**
 * Step 2: Services & FAQs Schema
 */
export const servicesStepSchema = z.object({
  services: z.array(serviceSchema).min(1, "At least one service is required"),
  faqs: z.string().optional(),
});

export type ServicesStepValues = z.infer<typeof servicesStepSchema>;

/**
 * Step 3: Scheduling Schema
 */
export const schedulingStepSchema = z.object({
  calendlyLink: z
    .string()
    .url("Please enter a valid Calendly URL")
    .min(1, "Calendly link is required"),
});

export type SchedulingStepValues = z.infer<typeof schedulingStepSchema>;

/**
 * Step 4: Channels (no validation needed, just completion)
 */
export type ChannelsStepValues = {
  webChat: boolean;
};

/**
 * Combined setup wizard data for final submission
 */
export type SetupWizardData = {
  profile: ProfileStepValues;
  services: ServicesStepValues;
  scheduling: SchedulingStepValues;
};
