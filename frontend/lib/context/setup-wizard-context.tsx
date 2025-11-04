"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import type {
  ProfileStepValues,
  ServicesStepValues,
  SchedulingStepValues,
  ChannelsStepValues,
  SetupWizardData,
} from "@/lib/validation/setup";

/**
 * Setup Wizard Context
 *
 * Manages state and navigation for the multi-step setup wizard.
 * Provides a reusable context for step navigation and data persistence.
 */

type WizardStep = 1 | 2 | 3 | 4;

interface WizardState {
  currentStep: WizardStep;
  profile: Partial<ProfileStepValues>;
  services: Partial<ServicesStepValues>;
  scheduling: Partial<SchedulingStepValues>;
  channels: Partial<ChannelsStepValues>;
}

interface WizardContextType {
  state: WizardState;
  updateProfile: (data: Partial<ProfileStepValues>) => void;
  updateServices: (data: Partial<ServicesStepValues>) => void;
  updateScheduling: (data: Partial<SchedulingStepValues>) => void;
  updateChannels: (data: Partial<ChannelsStepValues>) => void;
  goToStep: (step: WizardStep) => void;
  nextStep: () => void;
  prevStep: () => void;
  getWizardData: () => SetupWizardData | null;
  reset: () => void;
}

const SetupWizardContext = createContext<WizardContextType | undefined>(
  undefined
);

export function SetupWizardProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [state, setState] = useState<WizardState>({
    currentStep: 1,
    profile: {},
    services: {},
    scheduling: {},
    channels: { webChat: true },
  });

  const updateProfile = useCallback((data: Partial<ProfileStepValues>) => {
    setState((prev) => ({
      ...prev,
      profile: { ...prev.profile, ...data },
    }));
  }, []);

  const updateServices = useCallback((data: Partial<ServicesStepValues>) => {
    setState((prev) => ({
      ...prev,
      services: { ...prev.services, ...data },
    }));
  }, []);

  const updateScheduling = useCallback(
    (data: Partial<SchedulingStepValues>) => {
      setState((prev) => ({
        ...prev,
        scheduling: { ...prev.scheduling, ...data },
      }));
    },
    []
  );

  const updateChannels = useCallback((data: Partial<ChannelsStepValues>) => {
    setState((prev) => ({
      ...prev,
      channels: { ...prev.channels, ...data },
    }));
  }, []);

  const goToStep = useCallback((step: WizardStep) => {
    setState((prev) => ({ ...prev, currentStep: step }));
  }, []);

  const nextStep = useCallback(() => {
    setState((prev) => ({
      ...prev,
      currentStep: Math.min(prev.currentStep + 1, 4) as WizardStep,
    }));
  }, []);

  const prevStep = useCallback(() => {
    setState((prev) => ({
      ...prev,
      currentStep: Math.max(prev.currentStep - 1, 1) as WizardStep,
    }));
  }, []);

  const getWizardData = useCallback((): SetupWizardData | null => {
    if (
      !state.profile.profileType ||
      !state.profile.name ||
      !state.profile.tone ||
      !state.profile.timezone ||
      !state.profile.handle
    ) {
      return null;
    }

    if (!state.services.services || state.services.services.length === 0) {
      return null;
    }

    if (!state.scheduling.calendlyLink) {
      return null;
    }

    return {
      profile: state.profile as ProfileStepValues,
      services: state.services as ServicesStepValues,
      scheduling: state.scheduling as SchedulingStepValues,
    };
  }, [state]);

  const reset = useCallback(() => {
    setState({
      currentStep: 1,
      profile: {},
      services: {},
      scheduling: {},
      channels: { webChat: true },
    });
  }, []);

  const value: WizardContextType = {
    state,
    updateProfile,
    updateServices,
    updateScheduling,
    updateChannels,
    goToStep,
    nextStep,
    prevStep,
    getWizardData,
    reset,
  };

  return (
    <SetupWizardContext.Provider value={value}>
      {children}
    </SetupWizardContext.Provider>
  );
}

/**
 * Hook to use the setup wizard context
 */
export function useSetupWizard() {
  const context = useContext(SetupWizardContext);
  if (context === undefined) {
    throw new Error("useSetupWizard must be used within SetupWizardProvider");
  }
  return context;
}
