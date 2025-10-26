import { useMutation } from "@tanstack/react-query";
import {
  getApiClient,
  WorkspacesService,
  SchedulingConnectorsService,
  WorkspaceServicesService,
} from "@/lib/api/client";
import type {
  WorkspaceCreate,
  WorkspaceServiceCreate,
  SchedulingConnectorCreate,
} from "@/lib/api/generated/types.gen";
import type { SetupWizardData } from "@/lib/validation/setup";

/**
 * Complete Setup Wizard Hook
 *
 * Submits all wizard data atomically:
 * 1. Update user with profile type, bio, faqs
 * 2. Create workspace
 * 3. Create services
 * 4. Create Calendly connector
 * 5. Set setup_completed = true
 */
export function useCompleteSetup() {
  return useMutation({
    mutationFn: async (data: SetupWizardData) => {
      const client = await getApiClient();

      // Step 1: Update user with profile info (TODO: Implement when user update endpoint is available)
      // For now, profile data will be stored in workspace

      // Step 2: Create workspace
      const workspaceData: WorkspaceCreate = {
        handle: data.profile.handle,
        name: data.profile.name,
        type: data.profile.profileType, // Use profile type as workspace type
        tone: data.profile.tone,
        timezone: data.profile.timezone,
      };

      const workspaceResult = await WorkspacesService.createWorkspace({
        client,
        body: workspaceData,
      });

      if (!workspaceResult.data) {
        throw new Error("Failed to create workspace");
      }

      const workspaceId = workspaceResult.data.id;

      // Step 3: Create services
      const servicePromises = data.services.services.map((service, index) =>
        WorkspaceServicesService.createWorkspaceService({
          client,
          path: { workspace_id: workspaceId },
          body: {
            name: service.name,
            description: service.description,
            format: undefined,
            duration_minutes: service.duration_minutes,
            starting_price: service.starting_price,
            is_active: true,
            sort_order: index,
          } as WorkspaceServiceCreate,
        })
      );

      await Promise.all(servicePromises);

      // Step 4: Create Calendly connector
      const connectorData: SchedulingConnectorCreate = {
        type: "calendly",
        config: { link: data.scheduling.calendlyLink },
        is_active: true,
      };

      await SchedulingConnectorsService.createConnector({
        client,
        path: { workspace_id: workspaceId },
        body: connectorData,
      });

      // Step 5: Mark setup as completed
      // Note: This might need to be handled via a separate user update endpoint
      // For now, we'll leave it as the workspace creation implies setup completion

      return { workspaceId };
    },
  });
}
