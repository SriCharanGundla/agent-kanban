import { useState, useEffect } from "react";
import { toast } from "sonner";
import { tasksApi, membersApi } from "@/lib/api";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Task, TaskStatus, TaskPriority, ProjectMember } from "@/types";

interface NewTaskModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskCreated: (task: Task) => void;
  projectId: string;
  defaultStatus?: TaskStatus;
}

const STATUS_OPTIONS: { value: TaskStatus; label: string }[] = [
  { value: "backlog", label: "Backlog" },
  { value: "todo", label: "To Do" },
  { value: "in_progress", label: "In Progress" },
  { value: "done", label: "Done" },
];

const PRIORITY_OPTIONS: { value: TaskPriority; label: string }[] = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "urgent", label: "Urgent" },
];

export function NewTaskModal({
  open,
  onOpenChange,
  onTaskCreated,
  projectId,
  defaultStatus = "todo",
}: NewTaskModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<TaskStatus>(defaultStatus);
  const [priority, setPriority] = useState<TaskPriority>("medium");
  const [assigneeId, setAssigneeId] = useState<string | null>(null);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ title?: string }>({});

  // Sync status when modal opens or defaultStatus changes
  useEffect(() => {
    if (open) {
      setStatus(defaultStatus);
    }
  }, [open, defaultStatus]);

  // Fetch project members
  useEffect(() => {
    if (open && projectId) {
      membersApi
        .list(projectId)
        .then(setMembers)
        .catch((error) => {
          console.error("Failed to fetch members:", error);
        });
    }
  }, [open, projectId]);

  const handleClose = () => {
    if (!loading) {
      setTitle("");
      setDescription("");
      setStatus(defaultStatus);
      setPriority("medium");
      setAssigneeId(null);
      setErrors({});
      onOpenChange(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: { title?: string } = {};

    if (!title.trim()) {
      newErrors.title = "Task title is required";
    } else if (title.length > 500) {
      newErrors.title = "Task title must be less than 500 characters";
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
      const task = await tasksApi.create(projectId, {
        title: title.trim(),
        description: description.trim() || null,
        status,
        priority,
        assignee_id: assigneeId,
      });

      toast.success("Task created successfully!");
      onTaskCreated(task);
      handleClose();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to create task";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Task</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Field
            label="Title"
            invalid={!!errors.title}
            errorText={errors.title}
            required
          >
            <Input
              placeholder="Implement user authentication"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={loading}
              autoFocus
            />
          </Field>

          <div className="grid grid-cols-3 gap-4">
            <Field label="Status">
              <Select value={status} onValueChange={(val) => setStatus(val as TaskStatus)}>
                <SelectTrigger>
                  <SelectValue>
                    {STATUS_OPTIONS.find(o => o.value === status)?.label}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <Field label="Priority">
              <Select value={priority} onValueChange={(val) => setPriority(val as TaskPriority)}>
                <SelectTrigger>
                  <SelectValue>
                    {PRIORITY_OPTIONS.find(o => o.value === priority)?.label}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {PRIORITY_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <Field label="Assignee" helperText="Optional">
              <Select 
                value={assigneeId || "unassigned"} 
                onValueChange={(val) => setAssigneeId(val === "unassigned" ? null : val)}
              >
                <SelectTrigger>
                  <SelectValue>
                    {assigneeId 
                      ? members.find(m => m.user?.id === assigneeId)?.user?.full_name || "Unknown"
                      : "Unassigned"}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="unassigned">Unassigned</SelectItem>
                  {members.filter(m => m.user && m.status === "accepted").map((member) => (
                    <SelectItem key={member.user!.id} value={member.user!.id}>
                      {member.user!.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
          </div>

          <Field label="Description" helperText="Optional">
            <Textarea
              placeholder="Add a detailed description of the task..."
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
              {loading ? "Creating..." : "Create Task"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
