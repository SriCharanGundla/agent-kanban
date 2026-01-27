import { useState, useMemo } from "react";
import { Column } from "./Column";
import { NewTaskModal } from "./NewTaskModal";
import { TaskModal } from "./TaskModal";
import { Button } from "@/components/ui/button";
import type { Task, TaskStatus } from "@/types";

interface BoardProps {
  tasks: Task[];
  onTaskUpdate: (task: Task) => void;
  onTaskDelete: (taskId: string) => void;
  onTaskCreate: (task: Task) => void;
  projectId: string;
}

const COLUMNS: { status: TaskStatus; label: string }[] = [
  { status: "BACKLOG", label: "Backlog" },
  { status: "TODO", label: "To Do" },
  { status: "IN_PROGRESS", label: "In Progress" },
  { status: "DONE", label: "Done" },
];

export function Board({
  tasks,
  onTaskUpdate,
  onTaskDelete,
  onTaskCreate,
  projectId,
}: BoardProps) {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [newTaskModalOpen, setNewTaskModalOpen] = useState(false);
  const [newTaskStatus, setNewTaskStatus] = useState<TaskStatus>("TODO");

  // Precompute grouped and sorted tasks for better performance
  const tasksByStatus = useMemo(() => {
    const grouped: Record<TaskStatus, Task[]> = {
      BACKLOG: [],
      TODO: [],
      IN_PROGRESS: [],
      DONE: [],
    };

    // Group tasks by status
    for (const task of tasks) {
      grouped[task.status].push(task);
    }

    // Sort each group by position
    for (const status of Object.keys(grouped) as TaskStatus[]) {
      grouped[status].sort((a, b) => a.position - b.position);
    }

    return grouped;
  }, [tasks]);

  const handleAddTask = (status: TaskStatus) => {
    setNewTaskStatus(status);
    setNewTaskModalOpen(true);
  };

  return (
    <div className="space-y-4">
      {/* Add Task Button */}
      <div className="flex justify-end">
        <Button onClick={() => handleAddTask("TODO")}>+ Add Task</Button>
      </div>

      {/* Board Columns */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {COLUMNS.map((column) => (
          <Column
            key={column.status}
            status={column.status}
            label={column.label}
            tasks={tasksByStatus[column.status]}
            onTaskClick={setSelectedTask}
            onAddTask={handleAddTask}
          />
        ))}
      </div>

      {/* Task Detail Modal */}
      {selectedTask && (
        <TaskModal
          task={selectedTask}
          open={!!selectedTask}
          onOpenChange={(open) => !open && setSelectedTask(null)}
          onTaskUpdate={onTaskUpdate}
          onTaskDelete={(taskId) => {
            onTaskDelete(taskId);
            setSelectedTask(null);
          }}
        />
      )}

      {/* New Task Modal */}
      <NewTaskModal
        open={newTaskModalOpen}
        onOpenChange={setNewTaskModalOpen}
        onTaskCreated={onTaskCreate}
        projectId={projectId}
        defaultStatus={newTaskStatus}
      />
    </div>
  );
}
