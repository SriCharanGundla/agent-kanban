import { useState, useEffect } from "react";
import { toast } from "sonner";
import { AppLayout } from "@/components/layout/AppLayout";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { NewProjectModal } from "@/components/projects/NewProjectModal";
import { PendingInvitationsBanner } from "@/components/invitations/PendingInvitationsBanner";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useInvitations } from "@/hooks/useInvitations";
import { projectsApi } from "@/lib/api";
import type { ProjectWithStats } from "@/types";

export function Dashboard() {
  const [projects, setProjects] = useState<ProjectWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [newProjectModalOpen, setNewProjectModalOpen] = useState(false);
  
  // Fetch pending invitations
  const { invitations, isLoading: invitationsLoading, accept, decline } = useInvitations();

  const fetchData = async () => {
    try {
      setLoading(true);
      const projectsList = await projectsApi.list();
      setProjects(projectsList);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load projects";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleProjectCreated = (project: ProjectWithStats) => {
    setProjects((prev) => [...prev, project]);
  };

  // Calculate aggregate stats from project stats
  const totalTasks = projects.reduce((sum, project) => sum + project.task_count, 0);
  const completedTasks = projects.reduce((sum, project) => sum + project.done_count, 0);

  const getTaskStats = (projectId: string) => {
    const project = projects.find((p) => p.id === projectId);
    return {
      total: project?.task_count || 0,
      completed: project?.done_count || 0,
    };
  };

  const handleAcceptInvitation = async (token: string) => {
    const projectId = await accept(token);
    if (projectId) {
      // Refresh projects list after accepting invitation
      fetchData();
    }
    return projectId;
  };

  return (
    <AppLayout title="Dashboard">
      <div className="space-y-6">
        {/* Pending Invitations Banner */}
        {!invitationsLoading && invitations.length > 0 && (
          <PendingInvitationsBanner
            invitations={invitations}
            onAccept={handleAcceptInvitation}
            onDecline={decline}
          />
        )}

        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-3xl font-bold">Your Projects</h2>
          <Button onClick={() => setNewProjectModalOpen(true)}>
            + New Project
          </Button>
        </div>

        {/* Quick Stats */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <h3 className="text-sm font-medium text-muted-foreground">Projects</h3>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-3xl font-bold">{projects.length}</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-sm font-medium text-muted-foreground">Tasks</h3>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-3xl font-bold">{totalTasks}</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-sm font-medium text-muted-foreground">Completed</h3>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-3xl font-bold">{completedTasks}</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Projects Grid */}
        {loading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-4 w-full" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-2 w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : projects.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="text-6xl mb-4">📋</div>
              <h3 className="text-xl font-semibold mb-2">No projects yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first project to get started
              </p>
              <Button onClick={() => setNewProjectModalOpen(true)}>
                Create Project
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                taskStats={getTaskStats(project.id)}
              />
            ))}
            {/* New Project Card */}
            <Card
              className="flex cursor-pointer items-center justify-center border-dashed transition-colors hover:bg-accent/50"
              onClick={() => setNewProjectModalOpen(true)}
            >
              <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                <div className="text-5xl mb-2">➕</div>
                <h3 className="font-semibold">New Project</h3>
                <p className="text-sm text-muted-foreground">
                  Create a new project board
                </p>
              </CardContent>
            </Card>
          </div>
        )}
      </div>

      {/* New Project Modal */}
      <NewProjectModal
        open={newProjectModalOpen}
        onOpenChange={setNewProjectModalOpen}
        onProjectCreated={handleProjectCreated}
      />
    </AppLayout>
  );
}
