"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  Circle,
  Copy,
  Check,
  MessageSquare,
  Instagram,
  Smartphone,
  MessageCircle,
  Sparkles,
  Phone,
} from "lucide-react";
import { useSetupWizard } from "@/lib/context/setup-wizard-context";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";

/**
 * Step 4: Channels & Publish
 *
 * Review channels and publish the agent.
 */
export function ChannelsStep() {
  const { state, getWizardData, prevStep } = useSetupWizard();
  const [copied, setCopied] = useState(false);

  const wizardData = getWizardData();
  const profileHandle = state.profile.handle || "";

  const publicUrl = `${window.location.origin}/a/${profileHandle}`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(publicUrl);
    setCopied(true);
    toast.success("Link copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  const canPublish = () => {
    return (
      wizardData &&
      wizardData.profile.profileType &&
      wizardData.profile.name &&
      wizardData.profile.tone &&
      wizardData.profile.timezone &&
      wizardData.profile.handle &&
      wizardData.services.services &&
      wizardData.services.services.length > 0 &&
      wizardData.scheduling.calendlyLink
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Channels & Publish</CardTitle>
        <CardDescription>
          Review your channels and publish your agent
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Channels Section */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium">Available Channels</h3>

          {/* Web Chat - Enabled */}
          <Card>
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <MessageSquare className="h-5 w-5" />
                <div>
                  <div className="font-medium">Web Chat</div>
                  <div className="text-sm text-muted-foreground">
                    Inline chat widget for your website
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox checked disabled />
                <Badge variant="default">Active</Badge>
              </div>
            </div>
          </Card>

          {/* Coming Soon Channels */}
          <Card className="opacity-50">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <Instagram className="h-5 w-5" />
                <div>
                  <div className="font-medium">Instagram</div>
                  <div className="text-sm text-muted-foreground">
                    DMs on Instagram
                  </div>
                </div>
              </div>
              <Badge variant="secondary">Coming Soon</Badge>
            </div>
          </Card>

          <Card className="opacity-50">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <MessageCircle className="h-5 w-5" />
                <div>
                  <div className="font-medium">WhatsApp</div>
                  <div className="text-sm text-muted-foreground">
                    Chat on WhatsApp
                  </div>
                </div>
              </div>
              <Badge variant="secondary">Coming Soon</Badge>
            </div>
          </Card>

          <Card className="opacity-50">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <Smartphone className="h-5 w-5" />
                <div>
                  <div className="font-medium">SMS</div>
                  <div className="text-sm text-muted-foreground">
                    Text messaging
                  </div>
                </div>
              </div>
              <Badge variant="secondary">Coming Soon</Badge>
            </div>
          </Card>

          <Card className="opacity-50">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <MessageCircle className="h-5 w-5" />
                <div>
                  <div className="font-medium">Messenger</div>
                  <div className="text-sm text-muted-foreground">
                    Facebook Messenger
                  </div>
                </div>
              </div>
              <Badge variant="secondary">Coming Soon</Badge>
            </div>
          </Card>

          <Card className="opacity-50">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <Sparkles className="h-5 w-5" />
                <div>
                  <div className="font-medium">ChatGPT App</div>
                  <div className="text-sm text-muted-foreground">
                    Custom GPT in ChatGPT
                  </div>
                </div>
              </div>
              <Badge variant="secondary">Coming Soon</Badge>
            </div>
          </Card>

          <Card className="opacity-50">
            <div className="flex items-center justify-between p-4">
              <div className="flex items-center gap-3">
                <Phone className="h-5 w-5" />
                <div>
                  <div className="font-medium">Phone/Voice</div>
                  <div className="text-sm text-muted-foreground">
                    Voice conversations
                  </div>
                </div>
              </div>
              <Badge variant="secondary">Coming Soon</Badge>
            </div>
          </Card>
        </div>

        {/* Preview Section */}
        <div className="space-y-4 rounded-lg border p-6">
          <h3 className="text-sm font-medium">Public Agent URL</h3>
          <div className="flex items-center gap-2">
            <code className="flex-1 rounded bg-muted px-3 py-2 text-sm">
              {publicUrl}
            </code>
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={copyToClipboard}
            >
              {copied ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Ready to Publish Checklist */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium">Ready to Publish Checklist</h3>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {wizardData?.profile.profileType &&
              wizardData?.profile.name &&
              wizardData?.profile.tone &&
              wizardData?.profile.timezone &&
              wizardData?.profile.handle ? (
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              ) : (
                <Circle className="h-4 w-4" />
              )}
              <span className="text-sm">Profile complete</span>
            </div>
            <div className="flex items-center gap-2">
              {wizardData?.services.services &&
              wizardData.services.services.length > 0 ? (
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              ) : (
                <Circle className="h-4 w-4" />
              )}
              <span className="text-sm">At least one service added</span>
            </div>
            <div className="flex items-center gap-2">
              {wizardData?.scheduling.calendlyLink ? (
                <CheckCircle2 className="h-4 w-4 text-green-600" />
              ) : (
                <Circle className="h-4 w-4" />
              )}
              <span className="text-sm">Calendly connected</span>
            </div>
          </div>
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
          <Button
            type="button"
            disabled={!canPublish()}
            onClick={() => {
              // This will be handled by the parent component
              // trigger publish action
            }}
            className="flex-1"
          >
            Publish & Go Live
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
