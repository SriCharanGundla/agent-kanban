import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { invitationsApi } from "@/lib/api";
import { ApiError } from "@/lib/errors";
import type { PendingInvitation } from "@/types";

export function useInvitations() {
  const [invitations, setInvitations] = useState<PendingInvitation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInvitations = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await invitationsApi.list();
      setInvitations(data);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.userMessage
          : "Failed to load invitations";
      setError(message);
      // Don't show toast for initial load failures (might be auth issue)
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInvitations();
  }, [fetchInvitations]);

  const accept = useCallback(
    async (token: string): Promise<string | null> => {
      try {
        const response = await invitationsApi.accept(token);
        toast.success("Invitation accepted! Redirecting to project...");
        // Remove from local state
        setInvitations((prev) =>
          prev.filter((inv) => inv.token !== token)
        );
        return response.project_id;
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.userMessage
            : "Failed to accept invitation";
        toast.error(message);
        return null;
      }
    },
    []
  );

  const decline = useCallback(async (token: string): Promise<boolean> => {
    try {
      await invitationsApi.decline(token);
      toast.success("Invitation declined");
      // Remove from local state
      setInvitations((prev) =>
        prev.filter((inv) => inv.token !== token)
      );
      return true;
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.userMessage
          : "Failed to decline invitation";
      toast.error(message);
      return false;
    }
  }, []);

  return {
    invitations,
    isLoading,
    error,
    accept,
    decline,
    refresh: fetchInvitations,
  };
}
