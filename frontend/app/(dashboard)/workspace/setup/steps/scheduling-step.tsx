"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar, Link as LinkIcon } from "lucide-react";
import { useSetupWizard } from "@/lib/context/setup-wizard-context";
import {
  schedulingStepSchema,
  type SchedulingStepValues,
} from "@/lib/validation/setup";

/**
 * Step 3: Scheduling Connector
 *
 * Configure Calendly connector and show coming soon options.
 */
export function SchedulingStep() {
  const { state, updateScheduling, nextStep, prevStep } = useSetupWizard();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SchedulingStepValues>({
    resolver: zodResolver(schedulingStepSchema),
    defaultValues: {
      calendlyLink: state.scheduling.calendlyLink || "",
    },
  });

  const onSubmit = (data: SchedulingStepValues) => {
    updateScheduling(data);
    nextStep();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Scheduling Setup</CardTitle>
        <CardDescription>
          Connect your Calendly account to enable booking
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Calendly Card - Active */}
          <Card className="border-2 border-primary">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                <CardTitle className="text-lg">Calendly</CardTitle>
                <Badge variant="default">Available</Badge>
              </div>
              <CardDescription>
                Connect your personal Calendly scheduling link
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="calendlyLink">
                  Your Calendly Link <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="calendlyLink"
                  {...register("calendlyLink")}
                  placeholder="https://calendly.com/your-username"
                  aria-invalid={!!errors.calendlyLink}
                />
                {errors.calendlyLink && (
                  <p className="text-sm text-destructive">
                    {errors.calendlyLink.message}
                  </p>
                )}
                <p className="text-sm text-muted-foreground">
                  This is your personal Calendly scheduling link that the agent
                  will use to book meetings.
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Coming Soon Cards */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium">Coming Soon</h3>

            <Card className="opacity-50">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <LinkIcon className="h-5 w-5" />
                  <CardTitle className="text-lg">Square Appointments</CardTitle>
                  <Badge variant="secondary">Coming Soon</Badge>
                </div>
                <CardDescription>
                  Book appointments through Square Appointments
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="opacity-50">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <LinkIcon className="h-5 w-5" />
                  <CardTitle className="text-lg">AgendaPro</CardTitle>
                  <Badge variant="secondary">Coming Soon</Badge>
                </div>
                <CardDescription>
                  Integrate with AgendaPro scheduling platform
                </CardDescription>
              </CardHeader>
            </Card>
          </div>

          <div className="flex gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={prevStep}
              className="flex-1"
            >
              Back
            </Button>
            <Button type="submit" className="flex-1">
              Continue
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
