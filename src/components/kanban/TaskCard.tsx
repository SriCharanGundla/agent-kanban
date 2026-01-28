import { useRef, useEffect } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { User } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Task, TaskPriority } from "@/types";

interface TaskCardProps {
  task: Task;
  onClick: () => void;
}

const PRIORITY_STYLES: Record<
  TaskPriority,
  { label: string; className: string }
> = {
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
            <Badge className={`shrink-0 text-xs ${priority.className}`}>
              {priority.label}
            </Badge>
          </div>
          
          {task.description && (
            <p className="text-xs text-muted-foreground line-clamp-2">
              {task.description}
            </p>
          )}

          {task.assignee_name && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <User className="h-3 w-3" />
              <span>{task.assignee_name}</span>
            </div>
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
