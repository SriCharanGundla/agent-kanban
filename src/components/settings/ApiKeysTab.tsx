import { useState, useEffect } from "react";
import { toast } from "sonner";
import { apiKeysApi } from "@/lib/api";
import { NewApiKeyModal } from "./NewApiKeyModal";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
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
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { ApiKey } from "@/types";

export function ApiKeysTab() {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKeyModalOpen, setNewKeyModalOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [keyToDelete, setKeyToDelete] = useState<ApiKey | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchApiKeys = async () => {
    try {
      setLoading(true);
      const keys = await apiKeysApi.list();
      setApiKeys(keys);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load API keys";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const handleKeyCreated = () => {
    // Refetch the full list to get accurate server data
    fetchApiKeys();
  };

  const handleRevokeClick = (key: ApiKey) => {
    setKeyToDelete(key);
    setDeleteDialogOpen(true);
  };

  const handleRevokeConfirm = async () => {
    if (!keyToDelete) return;

    setDeleting(true);
    try {
      await apiKeysApi.delete(keyToDelete.id);
      setApiKeys((prev) => prev.filter((key) => key.id !== keyToDelete.id));
      toast.success("API key revoked successfully");
      setDeleteDialogOpen(false);
      setKeyToDelete(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to revoke API key";
      toast.error(message);
    } finally {
      setDeleting(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      if (diffHours === 0) {
        const diffMins = Math.floor(diffMs / (1000 * 60));
        return `${diffMins} minute${diffMins !== 1 ? "s" : ""} ago`;
      }
      return `${diffHours} hour${diffHours !== 1 ? "s" : ""} ago`;
    }
    if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? "s" : ""} ago`;
    return date.toLocaleDateString();
  };

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle>API Keys</CardTitle>
              <CardDescription className="mt-2">
                Generate API keys for your AI agents to access the Kanban board
                programmatically.
              </CardDescription>
            </div>
            <Button onClick={() => setNewKeyModalOpen(true)}>+ Generate Key</Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center justify-between border-b pb-3">
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-32" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                  <Skeleton className="h-8 w-16" />
                </div>
              ))}
            </div>
          ) : apiKeys.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="text-5xl mb-3">🔑</div>
              <h3 className="text-lg font-semibold mb-1">No API keys yet</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Generate your first API key to get started
              </p>
              <Button onClick={() => setNewKeyModalOpen(true)}>
                Generate API Key
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {apiKeys.map((key) => (
                <div
                  key={key.id}
                  className="flex items-center justify-between border-b pb-4 last:border-b-0"
                >
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-semibold">{key.name}</h4>
                      {!key.is_active && (
                        <span className="text-xs rounded bg-destructive/10 px-2 py-0.5 text-destructive">
                          Revoked
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground font-mono">
                      {key.key_prefix}...{key.key_suffix || '****'}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Last used: {formatDate(key.last_used_at)}
                    </p>
                  </div>
                  {key.is_active && (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleRevokeClick(key)}
                    >
                      Revoke
                    </Button>
                  )}
                </div>
              ))}

              {/* Warning */}
              <div className="mt-6 rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/20 p-4">
                <p className="text-sm font-medium text-amber-900 dark:text-amber-200">
                  ⚠️ Keep your API keys secure!
                </p>
                <p className="text-xs text-amber-800 dark:text-amber-300 mt-1">
                  API keys provide full access to your projects and tasks. Never share them
                  publicly or commit them to version control.
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* New API Key Modal */}
      <NewApiKeyModal
        open={newKeyModalOpen}
        onOpenChange={setNewKeyModalOpen}
        onApiKeyCreated={handleKeyCreated}
      />

      {/* Revoke Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Revoke API Key</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to revoke "{keyToDelete?.name}"? This action cannot be
              undone and any applications using this key will immediately lose access.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleRevokeConfirm} disabled={deleting}>
              {deleting ? "Revoking..." : "Revoke Key"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
