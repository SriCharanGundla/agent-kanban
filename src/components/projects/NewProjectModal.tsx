import { useState } from "react";
import { toast } from "sonner";
import { projectsApi } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { ProjectWithStats } from "@/types";

interface NewProjectModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onProjectCreated: (project: ProjectWithStats) => void;
}

export function NewProjectModal({
  open,
  onOpenChange,
  onProjectCreated,
}: NewProjectModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ name?: string; description?: string }>({});

  const handleClose = () => {
    if (!loading) {
      setName("");
      setDescription("");
      setErrors({});
      onOpenChange(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: { name?: string; description?: string } = {};

    if (!name.trim()) {
      newErrors.name = "Project name is required";
    } else if (name.length > 255) {
      newErrors.name = "Project name must be less than 255 characters";
    }

    if (description && description.length > 2000) {
      newErrors.description = "Description must be less than 2000 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      const project = await projectsApi.create({
        name: name.trim(),
        description: description.trim() || null,
      });
      
      toast.success("Project created successfully!");
      // New projects have no tasks yet
      onProjectCreated({ ...project, task_count: 0, done_count: 0 });
      handleClose();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to create project";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Field
            label="Project Name"
            invalid={!!errors.name}
            errorText={errors.name}
            required
          >
            <Input
              placeholder="Website Redesign"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={loading}
              autoFocus
            />
          </Field>

          <Field
            label="Description"
            helperText="Optional"
            invalid={!!errors.description}
            errorText={errors.description}
          >
            <Textarea
              placeholder="A complete overhaul of the company website..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={loading}
              rows={4}
            />
          </Field>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Create Project"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
