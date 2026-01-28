import { useState, useEffect, useRef } from "react";
import { Plus, User } from "lucide-react";
import { toast } from "sonner";
import type { DragEndEvent, DragStartEvent } from "@dnd-kit/core";
import {
  KanbanProvider,
  KanbanBoard,
  KanbanHeader,
  KanbanCards,
  KanbanCard,
} from "@/components/ui/kanban";
import { NewTaskModal } from "./NewTaskModal";
import { TaskModal } from "./TaskModal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { tasksApi } from "@/lib/api";
import type { Task, TaskStatus, TaskPriority } from "@/types";
import { cn } from "@/lib/utils";

interface BoardProps {
  tasks: Task[];
  onTaskUpdate: (task: Task) => void;
  onTaskDelete: (taskId: string) => void;
  onTaskCreate: (task: Task) => void;
  projectId: string;
}

// Adapter type: Map Task to KanbanItemProps format
interface KanbanTask extends Record<string, unknown> {
  id: string;
  name: string;      // maps to task.title
  column: string;    // maps to task.status
  task: Task;        // store original task for reference
}

// Column definitions
const COLUMNS = [
  { id: "backlog", name: "Backlog" },
  { id: "todo", name: "To Do" },
  { id: "in_progress", name: "In Progress" },
  { id: "done", name: "Done" },
];

// Priority styles (same as TaskCard)
const PRIORITY_STYLES: Record<TaskPriority, { label: string; className: string }> = {
  low: { 
    label: "Low", 
    className: "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800" 
  },
  medium: { 
    label: "Medium", 
    className: "bg-yellow-100 text-yellow-700 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800" 
  },
  high: { 
    label: "High", 
    className: "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:border-orange-800" 
  },
  urgent: { 
    label: "Urgent", 
    className: "bg-red-500 text-white border-red-600 dark:bg-red-600 dark:border-red-700" 
  },
};

export function Board({
  tasks,
  onTaskUpdate,
  onTaskDelete,
  onTaskCreate,
  projectId,
}: BoardProps) {
  // Modal state
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [newTaskModalOpen, setNewTaskModalOpen] = useState(false);
  const [newTaskStatus, setNewTaskStatus] = useState<TaskStatus>("todo");
  
  // Local state for kanban data - shadcn manages this during drag
  const [kanbanData, setKanbanData] = useState<KanbanTask[]>([]);
  
  // Track original task before drag for API calls
  const originalTaskRef = useRef<Task | null>(null);
  
  // SSR guard
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  // Sync tasks prop to kanbanData format whenever tasks change
  useEffect(() => {
    const data = tasks
      .slice() // Don't mutate original
      .sort((a, b) => a.position - b.position)
      .map((task) => ({
        id: task.id,
        name: task.title,
        column: task.status,
        task: task,
      }));
    setKanbanData(data);
  }, [tasks]);

  // Handle "Add Task" button click
  const handleAddTask = (status: TaskStatus) => {
    setNewTaskStatus(status);
    setNewTaskModalOpen(true);
  };

  // Handle task card click to open modal
  const handleCardClick = (task: Task) => {
    setSelectedTask(task);
  };

  // Track drag start to capture original state
  const handleDragStart = (event: DragStartEvent) => {
    const task = tasks.find((t) => t.id === event.active.id);
    originalTaskRef.current = task || null;
  };

  // Handle data changes during drag (shadcn manages this internally)
  const handleDataChange = (newData: KanbanTask[]) => {
    // Just update local state - shadcn handles the drag logic
    setKanbanData(newData);
  };

  // Handle drag end - only make API call to persist changes
  const handleDragEnd = async (event: DragEndEvent) => {
    const { active } = event;
    const originalTask = originalTaskRef.current;
    originalTaskRef.current = null;

    if (!originalTask) return;

    // Find the task in the updated kanbanData (shadcn already moved it)
    const movedItem = kanbanData.find((d) => d.id === active.id);
    if (!movedItem) return;

    const newStatus = movedItem.column as TaskStatus;
    const columnItems = kanbanData.filter((d) => d.column === newStatus);
    const newPosition = columnItems.findIndex((d) => d.id === active.id);

    // Check if anything actually changed
    const statusChanged = originalTask.status !== newStatus;
    const positionChanged = originalTask.position !== newPosition;

    if (!statusChanged && !positionChanged) return;

    // Optimistically update parent state
    const updatedTask: Task = {
      ...movedItem.task,
      status: newStatus,
      position: newPosition,
    };
    onTaskUpdate(updatedTask);

    // Make API call to persist
    try {
      const result = await tasksApi.reorder(active.id as string, {
        position: newPosition,
        status: statusChanged ? newStatus : undefined,
      });
      onTaskUpdate(result);
      
      if (statusChanged) {
        toast.success("Task moved successfully");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to move task";
      toast.error(message);
      // Rollback to original state
      onTaskUpdate(originalTask);
    }
  };

  // SSR loading state
  if (!mounted) {
    return <div className="h-96 w-full animate-pulse bg-muted/50" />;
  }

  return (
    <div className="space-y-4">
      {/* Add Task Button (top-level) */}
      <div className="flex justify-end">
        <Button onClick={() => handleAddTask("todo")}>
          <Plus className="h-5 w-5" />
          Add Task
        </Button>
      </div>

      {/* Kanban Board - shadcn handles layout with auto-cols-fr */}
      <KanbanProvider
        columns={COLUMNS}
        data={kanbanData}
        onDataChange={handleDataChange}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        className="h-[calc(100vh-16rem)]"
      >
        {(column) => (
          <KanbanBoard 
            id={column.id} 
            key={column.id}
            className="flex flex-col border bg-card"
          >
            {/* Column Header - match our styling */}
            <KanbanHeader className="flex items-center justify-between border-b p-4">
              <h3 className="font-semibold">
                {column.name}{" "}
                <span className="text-muted-foreground">
                  ({kanbanData.filter((d) => d.column === column.id).length})
                </span>
              </h3>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleAddTask(column.id as TaskStatus)}
                className="h-8 w-8 p-0"
              >
                <Plus className="h-5 w-5" />
              </Button>
            </KanbanHeader>

            {/* Task Cards - match our styling */}
            {(() => {
              const isEmpty = kanbanData.filter((d) => d.column === column.id).length === 0;
              return (
                <>
                  <KanbanCards 
                    id={column.id} 
                    className={cn("space-y-2", !isEmpty && "min-h-32")}
                  >
                    {(item: KanbanTask) => (
                      <KanbanCard
                        key={item.id}
                        id={item.id}
                        name={item.name}
                        column={item.column}
                        className="cursor-pointer hover:bg-accent/50"
                      >
                        {/* Custom card content - matches TaskCard */}
                        <div 
                          className="space-y-2"
                          onClick={() => handleCardClick(item.task)}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <h4 className="text-sm font-medium leading-tight line-clamp-2">
                              {item.task.title}
                            </h4>
                            <Badge className={`shrink-0 text-xs ${PRIORITY_STYLES[item.task.priority].className}`}>
                              {PRIORITY_STYLES[item.task.priority].label}
                            </Badge>
                          </div>
                          
                          {item.task.description && (
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {item.task.description}
                            </p>
                          )}

                          {item.task.assignee_name && (
                            <div className="flex items-center gap-1 text-xs text-muted-foreground">
                              <User className="h-3 w-3" />
                              <span>{item.task.assignee_name}</span>
                            </div>
                          )}

                          {item.task.subtasks && item.task.subtasks.length > 0 && (
                            <div className="flex justify-end">
                              <span className="text-xs text-muted-foreground">
                                {item.task.subtasks.filter((st) => st.is_completed).length}/
                                {item.task.subtasks.length} completed
                              </span>
                            </div>
                          )}
                        </div>
                      </KanbanCard>
                    )}
                  </KanbanCards>

                  {/* Empty state placeholder */}
                  {isEmpty && (
                    <div className="flex h-32 items-center justify-center">
                      <p className="text-sm text-muted-foreground">No tasks</p>
                    </div>
                  )}
                </>
              );
            })()}
          </KanbanBoard>
        )}
      </KanbanProvider>

      {/* Task Detail Modal */}
      {selectedTask && (
        <TaskModal
          task={selectedTask}
          projectId={projectId}
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
