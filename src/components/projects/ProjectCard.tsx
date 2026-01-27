import { Link } from "react-router-dom";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { Project } from "@/types";

interface ProjectCardProps {
  project: Project;
  taskStats?: {
    total: number;
    completed: number;
  };
}

export function ProjectCard({ project, taskStats }: ProjectCardProps) {
  const completionPercentage = taskStats && taskStats.total > 0
    ? Math.round((taskStats.completed / taskStats.total) * 100)
    : 0;

  const timeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    if (diffMins > 0) return `${diffMins}m ago`;
    return "just now";
  };

  return (
    <Link to={`/projects/${project.id}`}>
      <Card className="transition-colors hover:bg-accent/50">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <h3 className="text-lg font-semibold leading-none">{project.name}</h3>
              {project.description && (
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {project.description}
                </p>
              )}
            </div>
            <div className="text-3xl">📋</div>
          </div>
        </CardHeader>
        
        {taskStats && (
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                {taskStats.total} {taskStats.total === 1 ? "task" : "tasks"}
              </span>
              <span className="font-medium">{completionPercentage}%</span>
            </div>
            <Progress value={completionPercentage} />
          </CardContent>
        )}
        
        <CardFooter>
          <p className="text-xs text-muted-foreground">
            Updated {timeAgo(project.updated_at)}
          </p>
        </CardFooter>
      </Card>
    </Link>
  );
}
