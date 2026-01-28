import { useState, useEffect } from "react";
import { toast } from "sonner";
import { membersApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar } from "@/components/ui/avatar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { InviteMemberDialog } from "./InviteMemberDialog";
import { ApiError } from "@/lib/errors";
import type { ProjectMember, ProjectRole, Project, ProjectWithStats } from "@/types";

interface MembersTabProps {
  project: Project | ProjectWithStats;
  currentUserIsOwner: boolean;
  currentUserId: string;
}

export function MembersTab({
  project,
  currentUserIsOwner,
  currentUserId,
}: MembersTabProps) {
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [memberToRemove, setMemberToRemove] = useState<ProjectMember | null>(null);
  const [updatingMemberId, setUpdatingMemberId] = useState<string | null>(null);

  const fetchMembers = async () => {
    try {
      setLoading(true);
      const data = await membersApi.list(project.id);
      setMembers(data);
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.userMessage
          : "Failed to load members";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMembers();
  }, [project.id]);

  const handleRoleChange = async (memberId: string, newRole: ProjectRole) => {
    setUpdatingMemberId(memberId);
    try {
      const updated = await membersApi.updateRole(project.id, memberId, {
        role: newRole,
      });
      setMembers((prev) =>
        prev.map((m) => (m.id === memberId ? updated : m))
      );
      toast.success("Member role updated");
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.userMessage
          : "Failed to update role";
      toast.error(message);
    } finally {
      setUpdatingMemberId(null);
    }
  };

  const handleRemoveMember = async () => {
    if (!memberToRemove) return;

    try {
      await membersApi.remove(project.id, memberToRemove.id);
      setMembers((prev) => prev.filter((m) => m.id !== memberToRemove.id));
      toast.success(
        memberToRemove.user_id === currentUserId
          ? "You've left the project"
          : "Member removed"
      );
      setMemberToRemove(null);
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.userMessage
          : "Failed to remove member";
      toast.error(message);
    }
  };

  const getInitials = (name: string): string => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const getTimeUntilExpiry = (expiresAt: string): string => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry.getTime() - now.getTime();

    if (diffMs < 0) return "Expired";

    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (diffDays > 0) {
      return `${diffDays} day${diffDays > 1 ? "s" : ""}`;
    }
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    return `${diffHours} hour${diffHours > 1 ? "s" : ""}`;
  };

  const acceptedMembers = members.filter((m) => m.status === "accepted");
  const pendingMembers = members.filter((m) => m.status === "pending");
  const isOriginalCreator = (member: ProjectMember) =>
    member.user_id === project.owner_id;

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-9 w-32" />
        </div>
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-3 p-3 rounded-lg border">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div className="flex-1 space-y-1">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-48" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          Team Members ({acceptedMembers.length})
        </h3>
        {currentUserIsOwner && (
          <Button onClick={() => setInviteDialogOpen(true)} size="sm">
            + Invite Member
          </Button>
        )}
      </div>

      {/* Active Members */}
      <div className="space-y-2">
        {acceptedMembers.map((member) => {
          const isCurrentUser = member.user_id === currentUserId;
          const canRemove =
            currentUserIsOwner || isCurrentUser;
          const canChangeRole = currentUserIsOwner && !isOriginalCreator(member);

          return (
            <div
              key={member.id}
              className="flex items-center gap-3 p-3 rounded-lg border bg-card"
            >
              {/* Avatar */}
              <Avatar className="h-10 w-10 flex items-center justify-center bg-primary/10 text-primary font-semibold">
                {member.user ? getInitials(member.user.full_name) : "?"}
              </Avatar>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium truncate">
                    {member.user?.full_name || "Unknown"}
                    {isCurrentUser && (
                      <span className="text-muted-foreground ml-1">(You)</span>
                    )}
                  </p>
                  {isOriginalCreator(member) && (
                    <Badge variant="secondary" className="text-xs">
                      Creator
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-muted-foreground truncate">
                  {member.email}
                </p>
              </div>

              {/* Role */}
              {canChangeRole ? (
                <Select
                  value={member.role}
                  onValueChange={(value) =>
                    handleRoleChange(member.id, value as ProjectRole)
                  }
                  disabled={updatingMemberId === member.id}
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="owner">Owner</SelectItem>
                    <SelectItem value="member">Member</SelectItem>
                  </SelectContent>
                </Select>
              ) : (
                <Badge
                  variant={member.role === "owner" ? "default" : "secondary"}
                >
                  {member.role}
                </Badge>
              )}

              {/* Remove Button */}
              {canRemove && !isOriginalCreator(member) && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setMemberToRemove(member)}
                >
                  {isCurrentUser ? "Leave" : "Remove"}
                </Button>
              )}
            </div>
          );
        })}
      </div>

      {/* Pending Invitations */}
      {pendingMembers.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-muted-foreground">
            Pending Invitations ({pendingMembers.length})
          </h4>
          {pendingMembers.map((member) => {
            const isExpired = new Date(member.expires_at) < new Date();

            return (
              <div
                key={member.id}
                className="flex items-center gap-3 p-3 rounded-lg border bg-muted/30"
              >
                <Avatar className="h-10 w-10 flex items-center justify-center bg-muted text-muted-foreground font-semibold">
                  {getInitials(member.email)}
                </Avatar>

                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{member.email}</p>
                  <p className="text-xs text-muted-foreground">
                    {isExpired
                      ? "Expired"
                      : `Expires in ${getTimeUntilExpiry(member.expires_at)}`}
                  </p>
                </div>

                <Badge variant="secondary" className="text-xs">
                  Pending
                </Badge>

                {currentUserIsOwner && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setMemberToRemove(member)}
                  >
                    Cancel
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Invite Dialog */}
      <InviteMemberDialog
        open={inviteDialogOpen}
        onOpenChange={setInviteDialogOpen}
        projectId={project.id}
        onMemberInvited={fetchMembers}
      />

      {/* Remove Confirmation Dialog */}
      <AlertDialog
        open={!!memberToRemove}
        onOpenChange={(open) => !open && setMemberToRemove(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {memberToRemove?.user_id === currentUserId
                ? "Leave Project"
                : memberToRemove?.status === "pending"
                  ? "Cancel Invitation"
                  : "Remove Member"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {memberToRemove?.user_id === currentUserId
                ? "Are you sure you want to leave this project? You'll need to be re-invited to access it again."
                : memberToRemove?.status === "pending"
                  ? `Are you sure you want to cancel the invitation to ${memberToRemove.email}?`
                  : `Are you sure you want to remove ${memberToRemove?.user?.full_name || memberToRemove?.email} from this project?`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRemoveMember}>
              {memberToRemove?.user_id === currentUserId ? "Leave" : "Remove"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
