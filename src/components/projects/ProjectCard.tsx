import { Link } from "react-router-dom";
import { Users } from "lucide-react";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { ProjectWithStats } from "@/types";

interface ProjectCardProps {
  project: ProjectWithStats;
  taskStats?: {
    total: number;
    completed: number;
  };
}

export function ProjectCard({ project, taskStats }: ProjectCardProps) {
  // Use task stats from project if not provided separately
  const total = taskStats?.total ?? project.task_count;
  const completed = taskStats?.completed ?? project.done_count;
  
  const completionPercentage = total > 0
    ? Math.round((completed / total) * 100)
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
            <div className="space-y-1 flex-1">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold leading-none">{project.name}</h3>
                {project.user_role && (
                  <Badge variant={project.user_role === "owner" ? "default" : "secondary"} className="text-xs">
                    {project.user_role === "owner" ? "Owner" : "Member"}
                  </Badge>
                )}
              </div>
              {project.description && (
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {project.description}
                </p>
              )}
            </div>
            <div className="text-3xl">📋</div>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {total} {total === 1 ? "task" : "tasks"}
            </span>
            <span className="font-medium">{completionPercentage}%</span>
          </div>
          <Progress value={completionPercentage} />
          
          {project.member_count !== undefined && project.member_count > 1 && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground pt-1">
              <Users className="h-3 w-3" />
              <span>{project.member_count} {project.member_count === 1 ? "member" : "members"}</span>
            </div>
          )}
        </CardContent>
        
        <CardFooter>
          <p className="text-xs text-muted-foreground">
            Updated {timeAgo(project.updated_at)}
          </p>
        </CardFooter>
      </Card>
    </Link>
  );
}
