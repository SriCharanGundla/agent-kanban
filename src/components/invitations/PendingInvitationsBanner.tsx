import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { PendingInvitation } from "@/types";

interface PendingInvitationsBannerProps {
  invitations: PendingInvitation[];
  onAccept: (token: string) => Promise<string | null>;
  onDecline: (token: string) => Promise<boolean>;
}

export function PendingInvitationsBanner({
  invitations,
  onAccept,
  onDecline,
}: PendingInvitationsBannerProps) {
  const navigate = useNavigate();
  const [loadingTokens, setLoadingTokens] = useState<Set<string>>(new Set());

  if (invitations.length === 0) {
    return null;
  }

  const getTimeUntilExpiry = (expiresAt: string): string => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry.getTime() - now.getTime();

    if (diffMs < 0) return "Expired";

    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

    if (diffDays > 0) {
      return `Expires in ${diffDays} day${diffDays > 1 ? "s" : ""}`;
    }
    if (diffHours > 0) {
      return `Expires in ${diffHours} hour${diffHours > 1 ? "s" : ""}`;
    }
    return "Expires soon";
  };

  const handleAccept = async (token: string) => {
    setLoadingTokens((prev) => new Set(prev).add(token));
    try {
      const projectId = await onAccept(token);
      if (projectId) {
        navigate(`/projects/${projectId}`);
      }
    } finally {
      setLoadingTokens((prev) => {
        const next = new Set(prev);
        next.delete(token);
        return next;
      });
    }
  };

  const handleDecline = async (token: string) => {
    setLoadingTokens((prev) => new Set(prev).add(token));
    try {
      await onDecline(token);
    } finally {
      setLoadingTokens((prev) => {
        const next = new Set(prev);
        next.delete(token);
        return next;
      });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <h3 className="text-lg font-semibold">Pending Invitations</h3>
        <Badge variant="secondary">{invitations.length}</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {invitations.map((invitation) => {
          const isLoading = loadingTokens.has(invitation.token);
          const isExpired = new Date(invitation.expires_at) < new Date();

          return (
            <Card key={invitation.id} className="relative">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1 flex-1 min-w-0">
                    <h4 className="font-semibold leading-none truncate">
                      {invitation.project.name}
                    </h4>
                    <p className="text-sm text-muted-foreground">
                      Invited by {invitation.inviter.full_name}
                    </p>
                  </div>
                  <Badge
                    variant={invitation.role === "owner" ? "default" : "secondary"}
                  >
                    {invitation.role}
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="space-y-3">
                {invitation.project.description && (
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {invitation.project.description}
                  </p>
                )}

                <p className="text-xs text-muted-foreground">
                  {getTimeUntilExpiry(invitation.expires_at)}
                </p>

                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => handleAccept(invitation.token)}
                    disabled={isLoading || isExpired}
                    className="flex-1"
                  >
                    {isLoading ? "Accepting..." : "Accept"}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDecline(invitation.token)}
                    disabled={isLoading}
                    className="flex-1"
                  >
                    {isLoading ? "..." : "Decline"}
                  </Button>
                </div>

                {isExpired && (
                  <p className="text-xs text-destructive">
                    This invitation has expired
                  </p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
