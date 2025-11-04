"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  useWorkspaceServices,
  useCreateWorkspaceService,
  useUpdateWorkspaceService,
  useDeleteWorkspaceService,
} from "@/lib/api/hooks/use-workspace-services";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";
import type { WorkspaceServicePublic } from "@/lib/api/generated/types.gen";

/**
 * Service Form Schema
 */
const serviceFormSchema = z.object({
  name: z.string().min(1, "Service name is required"),
  description: z.string().optional(),
  duration_minutes: z.number().min(1).optional(),
  starting_price: z.number().min(0).optional(),
});

type ServiceFormValues = z.infer<typeof serviceFormSchema>;

interface ServicesSectionProps {
  workspaceId: string;
}

/**
 * Services Section
 *
 * Manages workspace services with full CRUD operations.
 * Includes add, edit, delete, and reorder functionality.
 */
export function ServicesSection({ workspaceId }: ServicesSectionProps) {
  const { data: services } = useWorkspaceServices(workspaceId);
  const createService = useCreateWorkspaceService(workspaceId);
  const updateService = useUpdateWorkspaceService();
  const deleteService = useDeleteWorkspaceService();
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [editingService, setEditingService] =
    useState<WorkspaceServicePublic | null>(null);

  const {
    register: addRegister,
    handleSubmit: addHandleSubmit,
    reset: addReset,
    formState: { errors: addErrors },
  } = useForm<ServiceFormValues>({
    resolver: zodResolver(serviceFormSchema),
  });

  const {
    register: editRegister,
    handleSubmit: editHandleSubmit,
    reset: editReset,
    formState: { errors: editErrors },
    setValue: editSetValue,
  } = useForm<ServiceFormValues>({
    resolver: zodResolver(serviceFormSchema),
  });

  const handleAddService = async (data: ServiceFormValues) => {
    try {
      const nextSortOrder = services ? services.length : 0;
      await createService.mutateAsync({
        name: data.name,
        description: data.description || undefined,
        duration_minutes: data.duration_minutes || undefined,
        starting_price: data.starting_price || undefined,
        is_active: true,
        sort_order: nextSortOrder,
      });
      toast.success("Service added successfully!");
      setIsAddDialogOpen(false);
      addReset();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to add service"
      );
    }
  };

  const handleEditService = async (data: ServiceFormValues) => {
    if (!editingService) return;

    try {
      await updateService.mutateAsync({
        serviceId: editingService.id,
        data: {
          name: data.name,
          description: data.description || undefined,
          duration_minutes: data.duration_minutes || undefined,
          starting_price: data.starting_price || undefined,
        },
      });
      toast.success("Service updated successfully!");
      setEditingService(null);
      editReset();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to update service"
      );
    }
  };

  const handleDeleteService = async (serviceId: string) => {
    try {
      await deleteService.mutateAsync(serviceId);
      toast.success("Service deleted successfully!");
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to delete service"
      );
    }
  };

  const openEditDialog = (service: WorkspaceServicePublic) => {
    setEditingService(service);
    editSetValue("name", service.name);
    editSetValue("description", service.description || "");
    editSetValue("duration_minutes", service.duration_minutes || undefined);
    // starting_price is stored as string in DB, parse it for form
    editSetValue(
      "starting_price",
      service.starting_price ? parseFloat(service.starting_price) : undefined
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Services</CardTitle>
            <CardDescription>Manage your service offerings</CardDescription>
          </div>
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Add Service
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Service</DialogTitle>
                <DialogDescription>
                  Create a new service offering for your workspace
                </DialogDescription>
              </DialogHeader>
              <form
                onSubmit={addHandleSubmit(handleAddService)}
                className="space-y-4"
              >
                <div className="space-y-2">
                  <Label htmlFor="name">Service Name *</Label>
                  <Input id="name" {...addRegister("name")} />
                  {addErrors.name && (
                    <p className="text-sm text-destructive">
                      {addErrors.name.message}
                    </p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea id="description" {...addRegister("description")} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="duration">Duration (minutes)</Label>
                  <Input
                    id="duration"
                    type="number"
                    {...addRegister("duration_minutes", {
                      valueAsNumber: true,
                    })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="price">Starting Price</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    {...addRegister("starting_price", {
                      valueAsNumber: true,
                    })}
                  />
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIsAddDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createService.isPending}>
                    {createService.isPending ? "Adding..." : "Add Service"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        {services && services.length > 0 ? (
          <div className="space-y-2">
            {services
              .sort((a, b) => a.sort_order - b.sort_order)
              .map((service) => (
                <div
                  key={service.id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="flex-1">
                    <p className="font-medium">{service.name}</p>
                    {service.description && (
                      <p className="text-sm text-muted-foreground">
                        {service.description}
                      </p>
                    )}
                    <div className="mt-2 flex gap-2">
                      {service.duration_minutes && (
                        <Badge variant="secondary">
                          {service.duration_minutes} min
                        </Badge>
                      )}
                      {service.starting_price && (
                        <Badge variant="secondary">
                          ${service.starting_price}
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => openEditDialog(service)}
                    >
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDeleteService(service.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No services yet</p>
        )}
      </CardContent>

      {/* Edit Dialog */}
      {editingService && (
        <Dialog
          open={!!editingService}
          onOpenChange={(open) => {
            if (!open) {
              setEditingService(null);
              editReset();
            }
          }}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Service</DialogTitle>
              <DialogDescription>Update the service details</DialogDescription>
            </DialogHeader>
            <form
              onSubmit={editHandleSubmit(handleEditService)}
              className="space-y-4"
            >
              <div className="space-y-2">
                <Label htmlFor="edit-name">Service Name *</Label>
                <Input id="edit-name" {...editRegister("name")} />
                {editErrors.name && (
                  <p className="text-sm text-destructive">
                    {editErrors.name.message}
                  </p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-description">Description</Label>
                <Textarea
                  id="edit-description"
                  {...editRegister("description")}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-duration">Duration (minutes)</Label>
                <Input
                  id="edit-duration"
                  type="number"
                  {...editRegister("duration_minutes", {
                    valueAsNumber: true,
                  })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-price">Starting Price</Label>
                <Input
                  id="edit-price"
                  type="number"
                  step="0.01"
                  {...editRegister("starting_price", {
                    valueAsNumber: true,
                  })}
                />
              </div>
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setEditingService(null);
                    editReset();
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={updateService.isPending}>
                  {updateService.isPending ? "Updating..." : "Update Service"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      )}
    </Card>
  );
}
