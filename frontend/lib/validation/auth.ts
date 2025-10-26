import { z } from "zod";

/**
 * Authentication Validation Schemas
 *
 * Zod schemas for validating login and signup forms.
 * Used with React Hook Form's zodResolver for type-safe form validation.
 */

/**
 * Login form validation schema
 * - email: Valid email address
 * - password: Minimum 6 characters
 */
export const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

/**
 * Type for login form values
 */
export type LoginFormValues = z.infer<typeof loginSchema>;

/**
 * Signup form validation schema
 * - email: Valid email address
 * - password: Minimum 6 characters
 * - confirmPassword: Must match password
 * - fullName: Optional string
 */
export const signupSchema = z
  .object({
    email: z.string().email("Please enter a valid email address"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    confirmPassword: z.string(),
    fullName: z.string().optional(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

/**
 * Type for signup form values
 */
export type SignupFormValues = z.infer<typeof signupSchema>;
