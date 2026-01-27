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
  LOW: { label: "Low", variant: "secondary" },
  MEDIUM: { label: "Medium", variant: "default" },
  HIGH: { label: "High", variant: "outline" },
  URGENT: { label: "Urgent", variant: "destructive" },
};

export function TaskCard({ task, onClick }: TaskCardProps) {
  const priority = PRIORITY_STYLES[task.priority];
  
  // Calculate subtask completion
  const subtasks = task.subtasks || [];
  const completedSubtasks = subtasks.filter((st) => st.is_completed).length;
  const hasSubtasks = subtasks.length > 0;

  return (
    <Card
      className="cursor-pointer transition-colors hover:bg-accent/50"
      onClick={onClick}
    >
      <CardHeader className="p-3">
        <div className="space-y-2">
          <div className="flex items-start justify-between gap-2">
            <h4 className="text-sm font-medium leading-tight line-clamp-2">
              {task.title}
            </h4>
            {task.priority !== "MEDIUM" && (
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
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="flex gap-0.5">
              {subtasks.map((subtask) => (
                <span key={subtask.id}>
                  {subtask.is_completed ? "☑" : "☐"}
                </span>
              ))}
            </div>
            <span>
              {completedSubtasks}/{subtasks.length}
            </span>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
