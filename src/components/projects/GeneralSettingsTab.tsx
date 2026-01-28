import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { projectsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { ApiError } from "@/lib/errors";
import type { Project } from "@/types";

interface GeneralSettingsTabProps {
  project: Project;
  onProjectUpdate: (project: Project) => void;
  currentUserIsOwner: boolean;
}

export function GeneralSettingsTab({
  project,
  onProjectUpdate,
  currentUserIsOwner,
}: GeneralSettingsTabProps) {
  const navigate = useNavigate();
  const [name, setName] = useState(project.name);
  const [description, setDescription] = useState(project.description || "");
  const [loading, setLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [errors, setErrors] = useState<{ name?: string; description?: string }>({});

  const hasChanges =
    name !== project.name || description !== (project.description || "");

  const validateForm = (): boolean => {
    const newErrors: { name?: string; description?: string } = {};

    if (!name.trim()) {
      newErrors.name = "Project name is required";
    } else if (name.length > 255) {
      newErrors.name = "Name must be less than 255 characters";
    }

    if (description.length > 5000) {
      newErrors.description = "Description must be less than 5000 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      const updated = await projectsApi.update(project.id, {
        name: name.trim(),
        description: description.trim() || null,
      });
      onProjectUpdate(updated);
      toast.success("Project updated successfully");
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.userMessage
          : "Failed to update project";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await projectsApi.delete(project.id);
      toast.success("Project deleted");
      navigate("/dashboard");
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.userMessage
          : "Failed to delete project";
      toast.error(message);
      setDeleteDialogOpen(false);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Project Details */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Project Details</h3>

        <Field
          label="Project Name"
          invalid={!!errors.name}
          errorText={errors.name}
          required
        >
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My Project"
            disabled={loading || !currentUserIsOwner}
          />
        </Field>

        <Field
          label="Description"
          invalid={!!errors.description}
          errorText={errors.description}
          helperText="Optional project description"
        >
          <Textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe your project..."
            rows={4}
            disabled={loading || !currentUserIsOwner}
          />
        </Field>

        {currentUserIsOwner && (
          <div className="flex gap-2">
            <Button
              onClick={handleSave}
              disabled={loading || !hasChanges}
            >
              {loading ? "Saving..." : "Save Changes"}
            </Button>
            {hasChanges && (
              <Button
                variant="outline"
                onClick={() => {
                  setName(project.name);
                  setDescription(project.description || "");
                  setErrors({});
                }}
                disabled={loading}
              >
                Cancel
              </Button>
            )}
          </div>
        )}

        {!currentUserIsOwner && (
          <p className="text-sm text-muted-foreground">
            Only project owners can edit project details.
          </p>
        )}
      </div>

      {/* Danger Zone */}
      {currentUserIsOwner && (
        <div className="space-y-4 pt-6 border-t border-destructive/20">
          <div>
            <h3 className="text-lg font-semibold text-destructive">Danger Zone</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Deleting a project is permanent and cannot be undone.
            </p>
          </div>

          <Button
            variant="destructive"
            onClick={() => setDeleteDialogOpen(true)}
          >
            Delete Project
          </Button>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Project</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{project.name}"? This action cannot be
              undone. All tasks and data associated with this project will be
              permanently deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-destructive hover:bg-destructive/90"
            >
              {deleting ? "Deleting..." : "Delete Project"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
