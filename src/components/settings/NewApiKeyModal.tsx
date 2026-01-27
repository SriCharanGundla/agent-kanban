import { useState } from "react";
import { toast } from "sonner";
import { apiKeysApi } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/errors";
import type { ApiKeyCreated } from "@/types";

interface NewApiKeyModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onApiKeyCreated: () => void;
}

export function NewApiKeyModal({
  open,
  onOpenChange,
  onApiKeyCreated,
}: NewApiKeyModalProps) {
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [errors, setErrors] = useState<{ name?: string }>({});

  const handleClose = () => {
    if (!loading) {
      setName("");
      setCreatedKey(null);
      setErrors({});
      onOpenChange(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: { name?: string } = {};

    if (!name.trim()) {
      newErrors.name = "API key name is required";
    } else if (name.length > 255) {
      newErrors.name = "Name must be less than 255 characters";
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
      const result = await apiKeysApi.create({
        name: name.trim(),
      });

      setCreatedKey(result);
      toast.success("API key created successfully!");

      // Just signal success - parent will refetch
      onApiKeyCreated();
    } catch (error) {
      // Handle ApiError with user-friendly messages
      if (error instanceof ApiError) {
        toast.error(error.userMessage);
      } else {
        toast.error("Failed to create API key. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (createdKey) {
      try {
        await navigator.clipboard.writeText(createdKey.key);
        toast.success("API key copied to clipboard!");
      } catch {
        toast.error("Failed to copy to clipboard");
      }
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent
        className={
          createdKey ? "w-fit min-w-96 max-w-[90vw] sm:max-w-[90vw]" : undefined
        }
      >
        {!createdKey ? (
          <>
            <DialogHeader>
              <DialogTitle>Generate New API Key</DialogTitle>
              <DialogDescription>
                Give your API key a descriptive name to identify it later.
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleSubmit} className="space-y-4">
              <Field
                label="Key Name"
                invalid={!!errors.name}
                errorText={errors.name}
                required
              >
                <Input
                  placeholder="My AI Agent"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={loading}
                  autoFocus
                />
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
                  {loading ? "Generating..." : "Generate API Key"}
                </Button>
              </DialogFooter>
            </form>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle>API Key Created!</DialogTitle>
              <DialogDescription>
                Copy this key now. You won't be able to see it again.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              <div className="rounded-lg border bg-muted p-4">
                <p className="break-all font-mono text-sm">{createdKey.key}</p>
              </div>

              <Button onClick={handleCopy} className="w-full">
                📋 Copy to Clipboard
              </Button>

              <div className="rounded-lg border p-4 text-sm">
                <p className="font-semibold mb-2">Usage Example:</p>
                <pre className="overflow-x-auto text-xs">
                  <code>{`curl -H "X-API-Key: ${createdKey.key}" \\
  ${window.location.origin}/api/v1/projects`}</code>
                </pre>
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
