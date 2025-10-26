"use client";

import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Plus, ArrowUp, ArrowDown, Trash2 } from "lucide-react";
import { useSetupWizard } from "@/lib/context/setup-wizard-context";
import {
  servicesStepSchema,
  type ServicesStepValues,
} from "@/lib/validation/setup";
import { Separator } from "@/components/ui/separator";

const PRE_SEEDED_SERVICES = [
  {
    name: "Consultation Call",
    description: "Initial consultation",
    duration_minutes: 30,
    starting_price: 0,
  },
  {
    name: "Audit",
    description: "Comprehensive audit",
    duration_minutes: 30,
    starting_price: 500,
  },
  {
    name: "Workshop",
    description: "Group workshop",
    duration_minutes: 30,
    starting_price: 1000,
  },
];

/**
 * Step 2: Services & FAQs
 *
 * Allows users to add/edit/remove services and optionally add FAQs.
 */
export function ServicesStep() {
  const { state, updateServices, nextStep, prevStep } = useSetupWizard();

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<ServicesStepValues>({
    resolver: zodResolver(servicesStepSchema),
    defaultValues: {
      services: state.services.services || PRE_SEEDED_SERVICES,
      faqs: state.services.faqs || "",
    },
  });

  const { fields, append, remove, move } = useFieldArray({
    control,
    name: "services",
  });

  const addService = () => {
    append({
      name: "",
      description: "",
      duration_minutes: undefined,
      starting_price: undefined,
    });
  };

  const onSubmit = (data: ServicesStepValues) => {
    updateServices(data);
    nextStep();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Services & FAQs</CardTitle>
        <CardDescription>
          Add your service offerings and frequently asked questions
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Services Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Services</Label>
              <Button
                type="button"
                onClick={addService}
                variant="outline"
                size="sm"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Service
              </Button>
            </div>

            {fields.map((field, index) => (
              <Card key={field.id} className="p-4">
                <div className="flex items-start gap-4">
                  <div className="flex flex-col gap-2 flex-1 space-y-2">
                    <div className="space-y-2">
                      <Label htmlFor={`services.${index}.name`}>
                        Service Name
                      </Label>
                      <Input
                        id={`services.${index}.name`}
                        {...register(`services.${index}.name`)}
                        placeholder="e.g., Consultation Call"
                        aria-invalid={!!errors.services?.[index]?.name}
                      />
                      {errors.services?.[index]?.name && (
                        <p className="text-sm text-destructive">
                          {errors.services[index]?.name?.message}
                        </p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor={`services.${index}.description`}>
                        Description (optional)
                      </Label>
                      <Input
                        id={`services.${index}.description`}
                        {...register(`services.${index}.description`)}
                        placeholder="Brief description"
                        aria-invalid={!!errors.services?.[index]?.description}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor={`services.${index}.duration_minutes`}>
                          Duration (minutes)
                        </Label>
                        <Input
                          id={`services.${index}.duration_minutes`}
                          type="number"
                          {...register(`services.${index}.duration_minutes`, {
                            valueAsNumber: true,
                          })}
                          placeholder="30"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor={`services.${index}.starting_price`}>
                          Starting Price ($)
                        </Label>
                        <Input
                          id={`services.${index}.starting_price`}
                          type="number"
                          step="0.01"
                          {...register(`services.${index}.starting_price`, {
                            valueAsNumber: true,
                          })}
                          placeholder="0.00"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => move(index, index - 1)}
                      disabled={index === 0}
                    >
                      <ArrowUp className="h-4 w-4" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => move(index, index + 1)}
                      disabled={index === fields.length - 1}
                    >
                      <ArrowDown className="h-4 w-4" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => remove(index)}
                      className="text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}

            {errors.services &&
              typeof errors.services === "object" &&
              "message" in errors.services && (
                <p className="text-sm text-destructive">
                  {errors.services.message as string}
                </p>
              )}
          </div>

          <Separator />

          {/* FAQs Section */}
          <div className="space-y-2">
            <Label htmlFor="faqs">FAQs (optional)</Label>
            <p className="text-sm text-muted-foreground">
              Paste your frequently asked questions and answers here. One Q&A
              pair per line.
            </p>
            <Textarea
              id="faqs"
              {...register("faqs")}
              placeholder="Q: What services do you offer?&#10;A: We offer consultation calls, audits, and workshops.&#10;&#10;Q: How do I book?&#10;A: Click the 'Book a Call' button below."
              rows={8}
              className="font-mono text-sm"
            />
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
