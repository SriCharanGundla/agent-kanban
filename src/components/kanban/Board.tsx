import { useState, useMemo } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  closestCorners,
} from "@dnd-kit/core";
import type { DragEndEvent, DragStartEvent } from "@dnd-kit/core";
import { arrayMove, sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { toast } from "sonner";
import { Column } from "./Column";
import { NewTaskModal } from "./NewTaskModal";
import { TaskModal } from "./TaskModal";
import { TaskCard } from "./TaskCard";
import { Button } from "@/components/ui/button";
import { tasksApi } from "@/lib/api";
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
  const [activeTask, setActiveTask] = useState<Task | null>(null);

  // Configure sensors for drag and drop
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement before drag starts (allows clicks)
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

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

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const task = tasks.find((t) => t.id === active.id);
    setActiveTask(task || null);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveTask(null);

    if (!over) return;

    const activeTaskId = active.id as string;
    const activeTaskData = tasks.find((t) => t.id === activeTaskId);
    if (!activeTaskData) return;

    // Determine target column and position
    let targetStatus: TaskStatus;
    let targetIndex: number;

    // Check if dropped directly on a column droppable or on a task
    const isColumnDrop = COLUMNS.some((c) => c.status === over.id);

    if (isColumnDrop) {
      // Dropped directly on column background
      targetStatus = over.id as TaskStatus;
      targetIndex = tasksByStatus[targetStatus].length;
    } else {
      // Dropped on a task - get the container from sortable context
      const overTaskId = over.id as string;
      const overTask = tasks.find((t) => t.id === overTaskId);
      
      if (!overTask) return;
      
      targetStatus = overTask.status;
      const tasksInTargetColumn = tasksByStatus[targetStatus];
      const overTaskIndex = tasksInTargetColumn.findIndex((t) => t.id === overTaskId);
      
      // Insert at the over task's position
      targetIndex = overTaskIndex >= 0 ? overTaskIndex : tasksInTargetColumn.length;
    }

    const tasksInTargetColumn = tasksByStatus[targetStatus];
    
    // Check if nothing changed
    if (activeTaskData.status === targetStatus) {
      const oldIndex = tasksInTargetColumn.findIndex((t) => t.id === activeTaskId);
      if (oldIndex === targetIndex || (oldIndex === targetIndex - 1)) {
        // Same position or adjacent (no real change)
        return;
      }
    }

    // Calculate new positions for all affected tasks
    const isSameColumn = activeTaskData.status === targetStatus;
    let updatedTasks: Task[] = [];

    if (isSameColumn) {
      // Reorder within same column
      const oldIndex = tasksInTargetColumn.findIndex((t) => t.id === activeTaskId);
      const reorderedTasks = arrayMove(tasksInTargetColumn, oldIndex, targetIndex);
      
      // Update positions for all tasks in this column
      updatedTasks = reorderedTasks.map((task, index) => ({
        ...task,
        position: index,
      }));
    } else {
      // Move to different column
      const sourceColumn = tasksByStatus[activeTaskData.status];
      const targetColumn = [...tasksInTargetColumn];
      
      // Insert task at target position
      targetColumn.splice(targetIndex, 0, {
        ...activeTaskData,
        status: targetStatus,
        position: targetIndex,
      });
      
      // Update positions for target column tasks
      const updatedTargetTasks = targetColumn.map((task, index) => ({
        ...task,
        position: index,
      }));
      
      // Update positions for source column tasks (if needed)
      const updatedSourceTasks = sourceColumn
        .filter((t) => t.id !== activeTaskId)
        .map((task, index) => ({
          ...task,
          position: index,
        }));
      
      updatedTasks = [...updatedSourceTasks, ...updatedTargetTasks];
    }

    // Apply optimistic updates
    updatedTasks.forEach((task) => onTaskUpdate(task));

    // Send API request for the dragged task
    try {
      const result = await tasksApi.reorder(activeTaskId, {
        position: isSameColumn 
          ? updatedTasks.find((t) => t.id === activeTaskId)!.position
          : targetIndex,
        status: isSameColumn ? undefined : targetStatus,
      });
      onTaskUpdate(result);
      
      if (!isSameColumn) {
        toast.success("Task moved successfully");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to move task";
      toast.error(message);
      
      // Rollback all optimistic updates
      onTaskUpdate(activeTaskData);
      // Note: This rollback is partial - ideally we'd restore all affected tasks
      // For full correctness, consider maintaining a snapshot of the previous state
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
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

      {/* Drag Overlay - shows a clone of the task being dragged */}
      <DragOverlay>
        {activeTask ? (
          <div className="rotate-3 cursor-grabbing">
            <TaskCard task={activeTask} onClick={() => {}} />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
