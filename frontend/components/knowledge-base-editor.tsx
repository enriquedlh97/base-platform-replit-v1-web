"use client";

import { useState, useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useUpdateWorkspace } from "@/lib/api/hooks/use-workspaces";
import {
  useWorkspaceConnectors,
  useCreateConnector,
  useUpdateConnector,
} from "@/lib/api/hooks/use-scheduling-connectors";
import { toast } from "sonner";
import { Loader2, Calendar } from "lucide-react";

interface KnowledgeBaseEditorProps {
  workspaceId: string;
  initialContent?: string | null;
}

export function KnowledgeBaseEditor({
  workspaceId,
  initialContent,
}: KnowledgeBaseEditorProps) {
  const [content, setContent] = useState(initialContent || "");
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  // Calendly form (RHF + Zod)
  const calendlySchema = z.object({
    calendlyLink: z.union([z.string().url(), z.literal("")]),
  });
  type CalendlyFormValues = z.infer<typeof calendlySchema>;

  const calendlyForm = useForm<CalendlyFormValues>({
    resolver: zodResolver(calendlySchema),
    defaultValues: { calendlyLink: "" },
    mode: "onChange",
  });

  const updateWorkspace = useUpdateWorkspace(workspaceId);
  const { data: connectors, isLoading: connectorsLoading } =
    useWorkspaceConnectors(workspaceId);
  const createConnector = useCreateConnector(workspaceId);
  const updateConnector = useUpdateConnector();

  // Find existing Calendly connector
  const calendlyConnector = useMemo(() => {
    if (!connectors) return null;
    return (
      connectors.find((connector) => connector.type === "calendly") || null
    );
  }, [connectors]);

  // Initialize Calendly link from existing connector
  useEffect(() => {
    const link = (calendlyConnector?.config?.link as string) || "";
    calendlyForm.reset({ calendlyLink: link }, { keepDirty: false });
  }, [calendlyConnector, calendlyForm]);

  // Update local state when initialContent changes (e.g., after loading)
  // Only update if the prop value is different from current state
  useEffect(() => {
    const newContent = initialContent || "";
    if (newContent !== content) {
      setContent(newContent);
      setHasUnsavedChanges(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialContent]);

  const handleSave = async () => {
    try {
      await updateWorkspace.mutateAsync({
        knowledge_base: content || null,
      });
      setHasUnsavedChanges(false);
      toast.success("Knowledge base saved successfully");
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to save knowledge base. Please try again."
      );
    }
  };

  const handleChange = (value: string) => {
    setContent(value);
    setHasUnsavedChanges(value !== (initialContent || ""));
  };

  const handleSaveCalendlyLink = calendlyForm.handleSubmit(async (values) => {
    try {
      const linkValue = values.calendlyLink.trim();
      const config = linkValue ? { link: linkValue } : {};

      if (calendlyConnector) {
        await updateConnector.mutateAsync({
          connectorId: calendlyConnector.id,
          data: {
            type: "calendly",
            config: linkValue ? config : null,
            is_active: linkValue ? true : false,
          },
        });
      } else if (linkValue) {
        await createConnector.mutateAsync({
          type: "calendly",
          config,
          is_active: true,
        });
      }

      calendlyForm.reset({ calendlyLink: linkValue }, { keepDirty: false });
      toast.success("Calendly link saved successfully");
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to save Calendly link. Please try again."
      );
    }
  });

  const characterCount = content.length;

  return (
    <div className="flex flex-1 flex-col gap-6">
      {/* Calendly Link Section */}
      <div className="flex flex-col gap-4 rounded-lg border p-4">
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-muted-foreground" />
          <Label htmlFor="calendly-link" className="text-base font-semibold">
            Calendly Scheduling Link
          </Label>
        </div>
        <p className="text-sm text-muted-foreground">
          Add your Calendly link so your AI agent can schedule appointments for
          customers.
        </p>
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <Input
              id="calendly-link"
              type="url"
              placeholder="https://calendly.com/username"
              aria-invalid={!!calendlyForm.formState.errors.calendlyLink}
              disabled={connectorsLoading}
              {...calendlyForm.register("calendlyLink")}
            />
            <Button
              onClick={handleSaveCalendlyLink}
              disabled={
                createConnector.isPending ||
                updateConnector.isPending ||
                !calendlyForm.formState.isDirty ||
                !!calendlyForm.formState.errors.calendlyLink ||
                connectorsLoading
              }
              size="default"
            >
              {createConnector.isPending || updateConnector.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save"
              )}
            </Button>
          </div>
          {calendlyForm.formState.errors.calendlyLink && (
            <p className="text-sm text-destructive">
              {calendlyForm.formState.errors.calendlyLink.message}
            </p>
          )}
          {calendlyForm.formState.isDirty &&
            !calendlyForm.formState.errors.calendlyLink && (
              <p className="text-sm text-muted-foreground">Unsaved changes</p>
            )}
        </div>
      </div>

      {/* Knowledge Base Section */}
      <div className="flex flex-1 flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Knowledge Base</h2>
            <p className="text-sm text-muted-foreground">
              Add information about your business that your AI agent can use to
              answer questions and assist customers.
            </p>
          </div>
          <div className="flex items-center gap-2">
            {hasUnsavedChanges && (
              <span className="text-sm text-muted-foreground">
                Unsaved changes
              </span>
            )}
            <Button
              onClick={handleSave}
              disabled={updateWorkspace.isPending || !hasUnsavedChanges}
            >
              {updateWorkspace.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save"
              )}
            </Button>
          </div>
        </div>

        <div className="flex flex-1 flex-col gap-2">
          <Textarea
            value={content}
            onChange={(e) => handleChange(e.target.value)}
            placeholder="Paste your business information here. Include details about your services, pricing, policies, FAQs, and any other information your AI agent should know..."
            className="min-h-[400px] flex-1 resize-none font-mono text-sm"
          />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              {characterCount === 0
                ? "No characters"
                : `${characterCount.toLocaleString()} character${characterCount === 1 ? "" : "s"}`}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
