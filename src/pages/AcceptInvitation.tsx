import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/context/AuthContext";
import { invitationsApi } from "@/lib/api";
import { ApiError, ErrorCode } from "@/lib/errors";

type AcceptState = "loading" | "success" | "error";

export function AcceptInvitation() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  const [state, setState] = useState<AcceptState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);

  useEffect(() => {
    // Wait for auth to load
    if (authLoading) {
      return;
    }

    // If not authenticated, redirect to login with redirect param
    if (!isAuthenticated) {
      navigate(`/login?redirect=/invitations/${token}`, { replace: true });
      return;
    }

    // If authenticated and have token, try to accept
    if (token) {
      acceptInvitation(token);
    } else {
      setState("error");
      setError("Invalid invitation link");
    }
  }, [authLoading, isAuthenticated, token, navigate]);

  const acceptInvitation = async (invitationToken: string) => {
    try {
      setState("loading");
      const response = await invitationsApi.accept(invitationToken);
      setProjectId(response.project_id);
      setState("success");
      // Redirect after a brief delay
      setTimeout(() => {
        navigate(`/projects/${response.project_id}`, { replace: true });
      }, 1500);
    } catch (err) {
      setState("error");
      
      if (err instanceof ApiError) {
        switch (err.code) {
          case ErrorCode.INVITATION_EXPIRED:
            setError("This invitation has expired. Please contact the project owner for a new invitation.");
            break;
          case ErrorCode.EMAIL_MISMATCH:
            setError("This invitation is for a different email address. Please log in with the correct account or contact the project owner.");
            break;
          case ErrorCode.INVITATION_NOT_FOUND:
            setError("This invitation link is invalid or has already been used.");
            break;
          case ErrorCode.ALREADY_MEMBER:
            setError("You are already a member of this project.");
            break;
          default:
            setError(err.userMessage);
        }
      } else {
        setError("Failed to accept invitation. Please try again or contact the project owner.");
      }
    }
  };

  // Show loading skeleton while auth is loading
  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <Card className="w-full max-w-md">
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-4 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        {state === "loading" && (
          <>
            <CardHeader>
              <h2 className="text-2xl font-bold text-center">Accepting Invitation</h2>
            </CardHeader>
            <CardContent className="flex flex-col items-center space-y-4">
              <div className="text-6xl animate-bounce">📨</div>
              <p className="text-muted-foreground text-center">
                Please wait while we add you to the project...
              </p>
            </CardContent>
          </>
        )}

        {state === "success" && (
          <>
            <CardHeader>
              <h2 className="text-2xl font-bold text-center text-green-600">
                Success!
              </h2>
            </CardHeader>
            <CardContent className="flex flex-col items-center space-y-4">
              <div className="text-6xl">✅</div>
              <p className="text-muted-foreground text-center">
                You've been added to the project. Redirecting...
              </p>
            </CardContent>
          </>
        )}

        {state === "error" && (
          <>
            <CardHeader>
              <h2 className="text-2xl font-bold text-center text-destructive">
                Unable to Accept Invitation
              </h2>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <div className="text-6xl mb-4">⚠️</div>
                <p className="text-muted-foreground">{error}</p>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={() => navigate("/dashboard")}
                  variant="outline"
                  className="flex-1"
                >
                  Go to Dashboard
                </Button>
                {token && (
                  <Button
                    onClick={() => {
                      setState("loading");
                      acceptInvitation(token);
                    }}
                    className="flex-1"
                  >
                    Try Again
                  </Button>
                )}
              </div>
            </CardContent>
          </>
        )}
      </Card>
    </div>
  );
}
