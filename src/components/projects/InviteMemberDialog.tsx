import { useState } from "react";
import { toast } from "sonner";
import { membersApi } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { ApiError, ErrorCode } from "@/lib/errors";
import type { ProjectRole } from "@/types";

interface InviteMemberDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
  onMemberInvited: () => void;
}

export function InviteMemberDialog({
  open,
  onOpenChange,
  projectId,
  onMemberInvited,
}: InviteMemberDialogProps) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<ProjectRole>("member");
  const [loading, setLoading] = useState(false);
  const [invitationLink, setInvitationLink] = useState<string | null>(null);
  const [errors, setErrors] = useState<{ email?: string }>({});

  const handleClose = () => {
    if (!loading) {
      setEmail("");
      setRole("member");
      setInvitationLink(null);
      setErrors({});
      onOpenChange(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: { email?: string } = {};

    if (!email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Please enter a valid email address";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      const result = await membersApi.invite(projectId, {
        email: email.trim(),
        role,
      });

      setInvitationLink(result.invitation_link);
      toast.success("Invitation created successfully!");
      onMemberInvited();
    } catch (error) {
      if (error instanceof ApiError) {
        switch (error.code) {
          case ErrorCode.ALREADY_MEMBER:
            setErrors({ email: "This user is already a member" });
            toast.error(error.userMessage);
            break;
          case ErrorCode.EMAIL_ALREADY_EXISTS:
            // User exists and has pending invite
            setErrors({ email: "An invitation has already been sent to this email" });
            toast.error("An invitation has already been sent to this email");
            break;
          default:
            toast.error(error.userMessage);
        }
      } else {
        toast.error("Failed to create invitation. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (invitationLink) {
      try {
        await navigator.clipboard.writeText(invitationLink);
        toast.success("Invitation link copied to clipboard!");
      } catch {
        toast.error("Failed to copy to clipboard");
      }
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent
        className={
          invitationLink ? "w-fit min-w-96 max-w-[90vw] sm:max-w-[90vw]" : undefined
        }
      >
        {!invitationLink ? (
          <>
            <DialogHeader>
              <DialogTitle>Invite Member</DialogTitle>
              <DialogDescription>
                Send an invitation to collaborate on this project.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleSubmit} className="space-y-4">
              <Field
                label="Email Address"
                invalid={!!errors.email}
                errorText={errors.email}
                required
              >
                <Input
                  type="email"
                  placeholder="colleague@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  autoFocus
                />
              </Field>

              <Field
                label="Role"
                helperText="Members can view and edit tasks. Owners can also manage project settings and members."
              >
                <Select
                  value={role}
                  onValueChange={(value) => setRole(value as ProjectRole)}
                  disabled={loading}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="member">Member</SelectItem>
                    <SelectItem value="owner">Owner</SelectItem>
                  </SelectContent>
                </Select>
              </Field>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClose}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={loading}>
                  {loading ? "Sending..." : "Send Invitation"}
                </Button>
              </DialogFooter>
            </form>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>Invitation Created!</DialogTitle>
              <DialogDescription>
                Share this link with the invitee. It will expire in 7 days.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              <div className="rounded-lg border bg-muted p-4">
                <p className="break-all font-mono text-sm">{invitationLink}</p>
              </div>

              <Button onClick={handleCopy} className="w-full">
                📋 Copy to Clipboard
              </Button>

              <div className="rounded-lg border p-4 text-sm space-y-2">
                <p className="font-semibold">Next Steps:</p>
                <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                  <li>Share this link with {email}</li>
                  <li>They can click the link to accept the invitation</li>
                  <li>If they don't have an account, they'll be prompted to create one</li>
                </ol>
              </div>
            </div>

            <DialogFooter>
              <Button onClick={handleClose}>Done</Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
