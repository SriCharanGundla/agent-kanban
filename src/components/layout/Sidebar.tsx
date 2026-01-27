import { useState, useEffect } from "react";
import { LayoutDashboard, Folder, Settings, ChevronDown, LogOut, User } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/context/AuthContext";
import { projectsApi } from "@/lib/api";
import type { ProjectWithStats } from "@/types";

export function AppSidebar() {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [projects, setProjects] = useState<ProjectWithStats[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(true);

  // Fetch projects when user changes
  useEffect(() => {
    // Clear projects if no user (logged out)
    if (!user) {
      setProjects([]);
      setLoadingProjects(false);
      return;
    }

    const abortController = new AbortController();
    let isMounted = true;

    const fetchProjects = async () => {
      try {
        setLoadingProjects(true);
        const fetchedProjects = await projectsApi.list();
        if (isMounted) {
          setProjects(fetchedProjects);
        }
      } catch (error) {
        if (isMounted) {
          console.error("Failed to fetch projects:", error);
        }
      } finally {
        if (isMounted) {
          setLoadingProjects(false);
        }
      }
    };

    fetchProjects();

    return () => {
      isMounted = false;
      abortController.abort();
    };
  }, [user?.id]);

  // Navigation items
  const navItems = [
    {
      title: "Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
    },
    {
      title: "Settings",
      href: "/settings",
      icon: Settings,
    },
  ];

  return (
    <Sidebar collapsible="icon">
      {/* Header */}
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <Link to="/dashboard" className="flex w-full">
              <SidebarMenuButton size="lg" className="w-full">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <Folder className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold">AgentKanban</span>
                  <span className="text-xs text-muted-foreground">Kanban for AI</span>
                </div>
              </SidebarMenuButton>
            </Link>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      {/* Content */}
      <SidebarContent>
        {/* Navigation */}
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <Link to={item.href} className="flex w-full">
                    <SidebarMenuButton isActive={location.pathname === item.href} className="w-full">
                      <item.icon />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  </Link>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Projects */}
        <SidebarGroup>
          <SidebarGroupLabel>Projects</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {loadingProjects ? (
                <SidebarMenuItem>
                  <SidebarMenuButton disabled>
                    <Folder className="opacity-50" />
                    <span className="text-muted-foreground">Loading...</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ) : projects.length === 0 ? (
                <SidebarMenuItem>
                  <SidebarMenuButton disabled>
                    <Folder className="opacity-50" />
                    <span className="text-muted-foreground">No projects yet</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ) : (
                projects.map((project) => (
                  <SidebarMenuItem key={project.id}>
                    <Link to={`/projects/${project.id}`} className="flex w-full">
                      <SidebarMenuButton
                        isActive={location.pathname === `/projects/${project.id}`}
                        className="w-full"
                      >
                        <Folder />
                        <span>{project.name}</span>
                      </SidebarMenuButton>
                    </Link>
                  </SidebarMenuItem>
                ))
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      {/* Footer */}
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger>
                <SidebarMenuButton render={<div />}>
                  <User />
                  <span>{user?.full_name || "User"}</span>
                  <ChevronDown className="ml-auto" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                side="top"
                className="w-[--radix-popper-anchor-width]"
              >
                <DropdownMenuItem disabled>
                  <User className="mr-2 size-4" />
                  <span>{user?.email}</span>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={logout}>
                  <LogOut className="mr-2 size-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
