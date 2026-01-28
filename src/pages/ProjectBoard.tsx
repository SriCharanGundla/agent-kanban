import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Settings, Users } from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { Board } from "@/components/kanban/Board";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { ProjectSettingsSheet } from "@/components/projects/ProjectSettingsSheet";
import { useAuth } from "@/context/AuthContext";
import { projectsApi, tasksApi } from "@/lib/api";
import type { ProjectWithStats, Task } from "@/types";

export function ProjectBoard() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [project, setProject] = useState<ProjectWithStats | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      if (!id) {
        navigate("/dashboard");
        return;
      }

      try {
        setLoading(true);
        const [projectData, tasksData] = await Promise.all([
          projectsApi.get(id),
          tasksApi.list(id),
        ]);
        setProject(projectData);
        setTasks(tasksData);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to load project";
        toast.error(message);
        navigate("/dashboard");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, navigate]);

  const handleTaskUpdate = (updatedTask: Task) => {
    setTasks(tasks.map((task) => (task.id === updatedTask.id ? updatedTask : task)));
  };

  const handleTaskDelete = (taskId: string) => {
    setTasks(tasks.filter((task) => task.id !== taskId));
  };

  const handleTaskCreate = (newTask: Task) => {
    setTasks([...tasks, newTask]);
  };

  const handleProjectUpdate = (updatedProject: ProjectWithStats | import("@/types").Project) => {
    // Preserve stats if they exist in the current project
    if (project && 'task_count' in updatedProject) {
      setProject(updatedProject as ProjectWithStats);
    } else if (project) {
      // Merge updated fields with existing stats
      setProject({
        ...updatedProject,
        task_count: project.task_count,
        done_count: project.done_count,
        user_role: project.user_role,
        member_count: project.member_count,
      });
    }
  };

  if (loading) {
    return (
      <AppLayout title="Loading...">
        <div className="space-y-4">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-96" />
            ))}
          </div>
        </div>
      </AppLayout>
    );
  }

  if (!project || !user) {
    return null;
  }

  // Check if current user is the project owner (prefer user_role if available)
  const currentUserIsOwner = project.user_role === "owner" || project.owner_id === user.id;

  return (
    <AppLayout title={project.name}>
      <div className="space-y-4">
        {/* Project Header */}
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1 min-w-0">
            <h2 className="text-3xl font-bold">{project.name}</h2>
            {project.description && (
              <p className="text-muted-foreground">{project.description}</p>
            )}
            {project.member_count !== undefined && project.member_count > 1 && (
              <div className="flex items-center gap-1 text-sm text-muted-foreground pt-1">
                <Users className="h-4 w-4" />
                <span>{project.member_count} {project.member_count === 1 ? "member" : "members"}</span>
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setSettingsOpen(true)}
              variant="outline"
              size="icon"
            >
              <Settings className="h-4 w-4" />
            </Button>
            <Button onClick={() => navigate("/dashboard")} variant="outline">
              Back to Dashboard
            </Button>
          </div>
        </div>

        {/* Kanban Board */}
        <Board
          tasks={tasks}
          onTaskUpdate={handleTaskUpdate}
          onTaskDelete={handleTaskDelete}
          onTaskCreate={handleTaskCreate}
          projectId={id!}
        />

        {/* Project Settings Sheet */}
        <ProjectSettingsSheet
          open={settingsOpen}
          onOpenChange={setSettingsOpen}
          project={project}
          onProjectUpdate={handleProjectUpdate}
          currentUserIsOwner={currentUserIsOwner}
          currentUserId={user.id}
        />
      </div>
    </AppLayout>
  );
}
