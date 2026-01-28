import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { Plus } from "lucide-react";
import { TaskCard } from "./TaskCard";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Task, TaskStatus } from "@/types";

interface ColumnProps {
  status: TaskStatus;
  label: string;
  tasks: Task[];
  onTaskClick: (task: Task) => void;
  onAddTask: (status: TaskStatus) => void;
}

export function Column({ status, label, tasks, onTaskClick, onAddTask }: ColumnProps) {
  const { setNodeRef, isOver } = useDroppable({
    id: status,
  });

  const taskIds = tasks.map((task) => task.id);

  return (
    <div className="flex flex-col rounded-lg border bg-card">
      {/* Column Header */}
      <div className="flex items-center justify-between border-b p-4">
        <h3 className="font-semibold">
          {label} <span className="text-muted-foreground">({tasks.length})</span>
        </h3>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => onAddTask(status)}
          className="h-8 w-8 p-0"
        >
          <Plus className="h-5 w-5" />
        </Button>
      </div>

      {/* Task List */}
      <ScrollArea className="flex-1 max-h-[calc(100vh-16rem)]">
        <div
          ref={setNodeRef}
          className={`space-y-2 p-2 min-h-32 transition-colors ${
            isOver ? "bg-accent/20" : ""
          }`}
        >
          <SortableContext items={taskIds} strategy={verticalListSortingStrategy}>
            {tasks.length === 0 ? (
              <div className="flex h-32 items-center justify-center">
                <p className="text-sm text-muted-foreground">No tasks</p>
              </div>
            ) : (
              tasks.map((task) => (
                <TaskCard key={task.id} task={task} onClick={() => onTaskClick(task)} />
              ))
            )}
          </SortableContext>
        </div>
      </ScrollArea>
    </div>
  );
}
