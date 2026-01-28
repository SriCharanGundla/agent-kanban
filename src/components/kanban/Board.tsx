import { useState, useMemo } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  pointerWithin,
  rectIntersection,
  closestCenter,
} from "@dnd-kit/core";
import type { 
  DragEndEvent, 
  DragStartEvent, 
  DragOverEvent, 
  CollisionDetection 
} from "@dnd-kit/core";
import { arrayMove, sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { Plus } from "lucide-react";
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
  { status: "backlog", label: "Backlog" },
  { status: "todo", label: "To Do" },
  { status: "in_progress", label: "In Progress" },
  { status: "done", label: "Done" },
];

// Custom collision detection that prioritizes column droppables for empty columns
const customCollisionDetection: CollisionDetection = (args) => {
  // First check pointer intersections
  const pointerCollisions = pointerWithin(args);
  
  // Find if we're over a column (status droppable)
  const columnIds = COLUMNS.map(c => c.status);
  const columnCollision = pointerCollisions.find(
    (collision) => columnIds.includes(collision.id as TaskStatus)
  );
  
  if (columnCollision) {
    // Check for task collisions within that column area
    const taskContainers = args.droppableContainers.filter(
      (container) => !columnIds.includes(container.id as TaskStatus)
    );
    
    // Use closestCenter to find nearest task, even when hovering in gaps
    const taskCollisions = closestCenter({
      ...args,
      droppableContainers: taskContainers,
    });
    
    // Return task collision if found, otherwise return column collision
    return taskCollisions.length > 0 ? taskCollisions : [columnCollision];
  }
  
  // Fallback to rect intersection for edge cases
  return rectIntersection(args);
};

export function Board({
  tasks,
  onTaskUpdate,
  onTaskDelete,
  onTaskCreate,
  projectId,
}: BoardProps) {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [newTaskModalOpen, setNewTaskModalOpen] = useState(false);
  const [newTaskStatus, setNewTaskStatus] = useState<TaskStatus>("todo");
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
      backlog: [],
      todo: [],
      in_progress: [],
      done: [],
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

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    
    if (!over) return;
    
    const activeTaskId = active.id as string;
    const activeTaskData = tasks.find((t) => t.id === activeTaskId);
    if (!activeTaskData) return;
    
    // Determine target column
    let targetStatus: TaskStatus;
    const isColumnDrop = COLUMNS.some((c) => c.status === over.id);
    
    if (isColumnDrop) {
      targetStatus = over.id as TaskStatus;
    } else {
      const overTask = tasks.find((t) => t.id === over.id);
      if (!overTask) return;
      targetStatus = overTask.status;
    }
    
    // If moving to different column, update optimistically during drag
    if (activeTaskData.status !== targetStatus) {
      onTaskUpdate({
        ...activeTaskData,
        status: targetStatus,
        // Set position to end of target column temporarily
        position: tasksByStatus[targetStatus].length,
      });
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    
    // Store original task data BEFORE clearing activeTask
    const originalTaskData = activeTask;
    setActiveTask(null);

    if (!over || !originalTaskData) return;

    const activeTaskId = active.id as string;

    // Determine target column and position
    let targetStatus: TaskStatus;
    let targetIndex: number;

    const isColumnDrop = COLUMNS.some((c) => c.status === over.id);

    if (isColumnDrop) {
      targetStatus = over.id as TaskStatus;
      targetIndex = tasksByStatus[targetStatus].filter(t => t.id !== activeTaskId).length;
    } else {
      const overTask = tasks.find((t) => t.id === over.id);
      if (!overTask) return;
      
      targetStatus = overTask.status;
      // Filter out the dragged task to get accurate index
      const tasksInColumn = tasksByStatus[targetStatus].filter(t => t.id !== activeTaskId);
      const overIndex = tasksInColumn.findIndex((t) => t.id === over.id);
      targetIndex = overIndex >= 0 ? overIndex : tasksInColumn.length;
    }

    // Get current state of the task (may have been updated by onDragOver)
    const currentTaskData = tasks.find((t) => t.id === activeTaskId);
    if (!currentTaskData) return;
    
    const sourceStatus = originalTaskData.status; // Use ORIGINAL status before drag
    const isSameColumn = sourceStatus === targetStatus;

    // Skip if dropped in same position
    if (isSameColumn) {
      const tasksInColumn = tasksByStatus[targetStatus];
      const currentIndex = tasksInColumn.findIndex((t) => t.id === activeTaskId);
      if (currentIndex === targetIndex || currentIndex === targetIndex - 1) {
        return;
      }
    }

    // Calculate and apply position updates
    let updatedTasks: Task[] = [];
    
    if (isSameColumn) {
      const tasksInColumn = [...tasksByStatus[targetStatus]];
      const oldIndex = tasksInColumn.findIndex((t) => t.id === activeTaskId);
      const reordered = arrayMove(tasksInColumn, oldIndex, targetIndex);
      updatedTasks = reordered.map((task, index) => ({ ...task, position: index }));
    } else {
      // Handle cross-column move
      const sourceColumn = tasksByStatus[sourceStatus]
        .filter((t) => t.id !== activeTaskId)
        .map((task, index) => ({ ...task, position: index }));
      
      const targetColumn = [...tasksByStatus[targetStatus].filter(t => t.id !== activeTaskId)];
      targetColumn.splice(targetIndex, 0, { ...currentTaskData, status: targetStatus });
      const updatedTarget = targetColumn.map((task, index) => ({ ...task, position: index }));
      
      updatedTasks = [...sourceColumn, ...updatedTarget];
    }

    // Apply optimistic updates
    updatedTasks.forEach((task) => onTaskUpdate(task));

    // API call
    try {
      const result = await tasksApi.reorder(activeTaskId, {
        position: targetIndex,
        status: isSameColumn ? undefined : targetStatus,
      });
      onTaskUpdate(result);
      
      if (!isSameColumn) {
        toast.success("Task moved successfully");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to move task";
      toast.error(message);
      // Rollback to original state
      onTaskUpdate(originalTaskData);
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={customCollisionDetection}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="space-y-4">
        {/* Add Task Button */}
        <div className="flex justify-end">
          <Button onClick={() => handleAddTask("todo")}>
            <Plus className="h-5 w-5" />
            Add Task
          </Button>
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
