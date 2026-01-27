import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { Board } from "@/components/kanban/Board";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { projectsApi, tasksApi } from "@/lib/api";
import type { Project, Task } from "@/types";

export function ProjectBoard() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleTaskUpdate = (updatedTask: Task) => {
    setTasks(tasks.map((task) => (task.id === updatedTask.id ? updatedTask : task)));
  };

  const handleTaskDelete = (taskId: string) => {
    setTasks(tasks.filter((task) => task.id !== taskId));
  };

  const handleTaskCreate = (newTask: Task) => {
    setTasks([...tasks, newTask]);
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

  if (!project) {
    return null;
  }

  return (
    <AppLayout title={project.name}>
      <div className="space-y-4">
        {/* Project Header */}
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <h2 className="text-3xl font-bold">{project.name}</h2>
            {project.description && (
              <p className="text-muted-foreground">{project.description}</p>
            )}
          </div>
          <Button onClick={() => navigate("/dashboard")} variant="outline">
            Back to Dashboard
          </Button>
        </div>

        {/* Kanban Board */}
        <Board
          tasks={tasks}
          onTaskUpdate={handleTaskUpdate}
          onTaskDelete={handleTaskDelete}
          onTaskCreate={handleTaskCreate}
          projectId={id!}
        />
      </div>
    </AppLayout>
  );
}
