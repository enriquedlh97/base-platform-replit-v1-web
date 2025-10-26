import { z } from "zod";

/**
 * Workspace Validation Schemas
 *
 * Zod schemas for validating workspace forms.
 * Used with React Hook Form's zodResolver for type-safe form validation.
 */

/**
 * Workspace creation/update validation schema
 */
export const workspaceSchema = z.object({
  handle: z
    .string()
    .min(3, "Handle must be at least 3 characters")
    .max(100, "Handle must be less than 100 characters")
    .regex(
      /^[a-z0-9-]+$/,
      "Handle can only contain lowercase letters, numbers, and hyphens"
    ),
  name: z
    .string()
    .min(1, "Name is required")
    .max(255, "Name must be less than 255 characters"),
  type: z.string().min(1, "Type is required"),
  tone: z.string().min(1, "Tone is required"),
  timezone: z.string().min(1, "Timezone is required"),
});

/**
 * Type for workspace form values
 */
export type WorkspaceFormValues = z.infer<typeof workspaceSchema>;
