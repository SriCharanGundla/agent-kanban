import { useState, useEffect } from "react";
import { X } from "lucide-react";
import { toast } from "sonner";
import { tasksApi, subtasksApi } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
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
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import type { Task, Subtask, TaskStatus, TaskPriority } from "@/types";

interface TaskModalProps {
  task: Task;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskUpdate: (task: Task) => void;
  onTaskDelete: (taskId: string) => void;
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

export function TaskModal({
  task,
  open,
  onOpenChange,
  onTaskUpdate,
  onTaskDelete,
}: TaskModalProps) {
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description || "");
  const [status, setStatus] = useState<TaskStatus>(task.status);
  const [priority, setPriority] = useState<TaskPriority>(task.priority);
  const [subtasks, setSubtasks] = useState<Subtask[]>(task.subtasks || []);
  const [newSubtaskTitle, setNewSubtaskTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  useEffect(() => {
    setTitle(task.title);
    setDescription(task.description || "");
    setStatus(task.status);
    setPriority(task.priority);
    setSubtasks(task.subtasks || []);
  }, [task]);

  const handleSave = async () => {
    if (!title.trim()) {
      toast.warning("Task title is required");
      return;
    }

    setLoading(true);
    try {
      const updatedTask = await tasksApi.update(task.id, {
        title: title.trim(),
        description: description.trim() || null,
        status,
        priority,
      });
      updatedTask.subtasks = subtasks;
      onTaskUpdate(updatedTask);
      toast.success("Task updated successfully");
      onOpenChange(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to update task";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    setLoading(true);
    try {
      await tasksApi.delete(task.id);
      toast.success("Task deleted successfully");
      onTaskDelete(task.id);
      setDeleteDialogOpen(false);
      onOpenChange(false);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to delete task";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSubtask = async () => {
    if (!newSubtaskTitle.trim()) {
      return;
    }

    try {
      const subtask = await subtasksApi.create(task.id, {
        title: newSubtaskTitle.trim(),
      });
      setSubtasks((prev) => [...prev, subtask]);
      setNewSubtaskTitle("");
      toast.success("Subtask added");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to add subtask";
      toast.error(message);
    }
  };

  const handleToggleSubtask = async (subtask: Subtask) => {
    try {
      const updated = await subtasksApi.update(subtask.id, {
        is_completed: !subtask.is_completed,
      });
      setSubtasks((prev) => prev.map((st) => (st.id === subtask.id ? updated : st)));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to update subtask";
      toast.error(message);
    }
  };

  const handleDeleteSubtask = async (subtaskId: string) => {
    try {
      await subtasksApi.delete(subtaskId);
      setSubtasks((prev) => prev.filter((st) => st.id !== subtaskId));
      toast.success("Subtask deleted");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to delete subtask";
      toast.error(message);
    }
  };

  const completedSubtasks = subtasks.filter((st) => st.is_completed).length;
  const progressPercentage = subtasks.length > 0
    ? Math.round((completedSubtasks / subtasks.length) * 100)
    : 0;

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Task Details</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            {/* Title */}
            <Field label="Title" required>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                disabled={loading}
              />
            </Field>

            {/* Status and Priority */}
            <div className="grid grid-cols-2 gap-4">
              <Field label="Status">
                <Select value={status} onValueChange={(val) => setStatus(val as TaskStatus)}>
                  <SelectTrigger>
                    <SelectValue />
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
                    <SelectValue />
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
            </div>

            {/* Description */}
            <Field label="Description" helperText="Optional">
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={loading}
                rows={4}
              />
            </Field>

            {/* Subtasks */}
            <div className="space-y-2">
              <Field label="Subtasks" helperText={`${completedSubtasks}/${subtasks.length} completed`}>
                <div className="space-y-3">
                  {subtasks.length > 0 && (
                    <ScrollArea className="max-h-48 rounded-md border">
                      <div className="space-y-1 p-2">
                        {subtasks.map((subtask) => (
                          <div
                            key={subtask.id}
                            className="flex items-center gap-3 rounded-md border bg-card p-3 transition-colors hover:bg-accent/50"
                          >
                            <Checkbox
                              checked={subtask.is_completed}
                              onCheckedChange={() => handleToggleSubtask(subtask)}
                              className="shrink-0"
                            />
                            <span
                              className={`flex-1 text-sm ${
                                subtask.is_completed ? "line-through text-muted-foreground" : ""
                              }`}
                            >
                              {subtask.title}
                            </span>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDeleteSubtask(subtask.id)}
                              className="h-8 w-8 shrink-0 p-0 text-destructive hover:bg-destructive/10"
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  )}
                  
                  {/* Add Subtask */}
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add a subtask..."
                      value={newSubtaskTitle}
                      onChange={(e) => setNewSubtaskTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          handleAddSubtask();
                        }
                      }}
                    />
                    <Button
                      type="button"
                      size="sm"
                      onClick={handleAddSubtask}
                      disabled={!newSubtaskTitle.trim()}
                    >
                      Add
                    </Button>
                  </div>
                </div>
              </Field>

              {/* Progress */}
              {subtasks.length > 0 && (
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Progress</span>
                    <span className="font-medium">{progressPercentage}%</span>
                  </div>
                  <Progress value={progressPercentage} />
                </div>
              )}
            </div>

            {/* Timestamps */}
            <div className="text-xs text-muted-foreground">
              <p>Created: {new Date(task.created_at).toLocaleString()}</p>
              <p>Updated: {new Date(task.updated_at).toLocaleString()}</p>
            </div>
          </div>

          <DialogFooter className="flex justify-between">
            <Button
              type="button"
              variant="destructive"
              onClick={() => setDeleteDialogOpen(true)}
              disabled={loading}
            >
              Delete
            </Button>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={loading}>
                {loading ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Task</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this task? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={loading}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} disabled={loading}>
              {loading ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
