"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  SetupWizardProvider,
  useSetupWizard,
} from "@/lib/context/setup-wizard-context";
import { ProfileStep } from "./steps/profile-step";
import { ServicesStep } from "./steps/services-step";
import { SchedulingStep } from "./steps/scheduling-step";
import { ChannelsStep } from "./steps/channels-step";
import { Progress } from "@/components/ui/progress";
import { useCompleteSetup } from "@/lib/api/hooks/use-setup-wizard";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  ProfileStepValues,
  ServicesStepValues,
  SchedulingStepValues,
} from "@/lib/validation/setup";

/**
 * Main Setup Wizard Container
 *
 * Orchestrates the 4-step setup wizard with progress indicator and navigation.
 */
function SetupWizardContent() {
  const { state } = useSetupWizard();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const completeSetup = useCompleteSetup();

  const steps = [
    { title: "Profile", description: "Basic information" },
    { title: "Services", description: "Offerings & FAQs" },
    { title: "Scheduling", description: "Calendly setup" },
    { title: "Channels", description: "Publish & go live" },
  ];

  const currentStep = state.currentStep;
  const progress = ((currentStep - 1) / (steps.length - 1)) * 100;

  const handlePublish = async () => {
    setIsLoading(true);
    try {
      await completeSetup.mutateAsync({
        profile: state.profile as ProfileStepValues,
        services: state.services as ServicesStepValues,
        scheduling: state.scheduling as SchedulingStepValues,
      });

      toast.success("Your agent is live!");
      router.push("/dashboard");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to publish agent"
      );
      setIsLoading(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <ProfileStep />;
      case 2:
        return <ServicesStep />;
      case 3:
        return <SchedulingStep />;
      case 4:
        return (
          <div>
            <ChannelsStep />
            <div className="mt-4 flex justify-end">
              <button
                onClick={handlePublish}
                disabled={isLoading}
                className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:pointer-events-none"
              >
                {isLoading ? "Publishing..." : "Publish & Go Live"}
              </button>
            </div>
          </div>
        );
      default:
        return <ProfileStep />;
    }
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <Skeleton className="h-64" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Progress Indicator */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">
            Step {currentStep} of {steps.length}
          </span>
          <span className="text-muted-foreground">
            {steps[currentStep - 1].title}
          </span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Step Navigation Breadcrumbs */}
      <div className="flex gap-2">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`flex-1 rounded-lg border p-3 text-center text-sm ${
              index + 1 <= currentStep
                ? "border-primary bg-primary/10"
                : "border-muted"
            }`}
          >
            <div className="font-medium">{step.title}</div>
            <div className="text-xs text-muted-foreground">
              {step.description}
            </div>
          </div>
        ))}
      </div>

      {/* Step Content */}
      {renderStep()}
    </div>
  );
}

export default function SetupWizardPage() {
  return (
    <SetupWizardProvider>
      <SetupWizardContent />
    </SetupWizardProvider>
  );
}
