"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateWorkspace } from "@/lib/api/hooks/use-workspaces";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

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

  const updateWorkspace = useUpdateWorkspace(workspaceId);

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

  const characterCount = content.length;

  return (
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
  );
}
