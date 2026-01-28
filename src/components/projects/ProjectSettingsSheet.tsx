import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { GeneralSettingsTab } from "./GeneralSettingsTab";
import { MembersTab } from "./MembersTab";
import type { Project, ProjectWithStats } from "@/types";

interface ProjectSettingsSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  project: ProjectWithStats;
  onProjectUpdate: (project: Project | ProjectWithStats) => void;
  currentUserIsOwner: boolean;
  currentUserId: string;
}

export function ProjectSettingsSheet({
  open,
  onOpenChange,
  project,
  onProjectUpdate,
  currentUserIsOwner,
  currentUserId,
}: ProjectSettingsSheetProps) {
  const [activeTab, setActiveTab] = useState("general");

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-2xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Project Settings</SheetTitle>
          <SheetDescription>
            Manage your project settings and team members.
          </SheetDescription>
        </SheetHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="general">General</TabsTrigger>
            <TabsTrigger value="members">Members</TabsTrigger>
          </TabsList>

          <TabsContent value="general" className="mt-6">
            <GeneralSettingsTab
              project={project}
              onProjectUpdate={onProjectUpdate}
              currentUserIsOwner={currentUserIsOwner}
            />
          </TabsContent>

          <TabsContent value="members" className="mt-6">
            <MembersTab
              project={project}
              currentUserIsOwner={currentUserIsOwner}
              currentUserId={currentUserId}
            />
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}
