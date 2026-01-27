import { useRef, useEffect } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Task, TaskPriority } from "@/types";

interface TaskCardProps {
  task: Task;
  onClick: () => void;
}

const PRIORITY_STYLES: Record<
  TaskPriority,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  low: { label: "Low", variant: "secondary" },
  medium: { label: "Medium", variant: "default" },
  high: { label: "High", variant: "outline" },
  urgent: { label: "Urgent", variant: "destructive" },
};

export function TaskCard({ task, onClick }: TaskCardProps) {
  const priority = PRIORITY_STYLES[task.priority];
  
  // Calculate subtask completion
  const subtasks = task.subtasks || [];
  const completedSubtasks = subtasks.filter((st) => st.is_completed).length;
  const hasSubtasks = subtasks.length > 0;

  // Setup drag and drop
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: task.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  // Prevent click immediately after drag
  const wasDragging = useRef(false);
  
  useEffect(() => {
    if (isDragging) {
      wasDragging.current = true;
    }
  }, [isDragging]);

  const handleClick = () => {
    if (wasDragging.current) {
      wasDragging.current = false;
      return;
    }
    onClick();
  };

  return (
    <Card
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="cursor-grab active:cursor-grabbing transition-colors hover:bg-accent/50"
      onClick={handleClick}
    >
      <CardHeader className="p-3">
        <div className="space-y-2">
          <div className="flex items-start justify-between gap-2">
            <h4 className="text-sm font-medium leading-tight line-clamp-2">
              {task.title}
            </h4>
            {task.priority !== "medium" && (
              <Badge variant={priority.variant} className="shrink-0 text-xs">
                {priority.label}
              </Badge>
            )}
          </div>
          
          {task.description && (
            <p className="text-xs text-muted-foreground line-clamp-2">
              {task.description}
            </p>
          )}
        </div>
      </CardHeader>

      {hasSubtasks && (
        <CardContent className="p-3 pt-0">
          <div className="flex justify-end">
            <span className="text-xs text-muted-foreground">
              {completedSubtasks}/{subtasks.length} completed
            </span>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
