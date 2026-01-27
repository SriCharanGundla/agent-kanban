import { AppLayout } from "@/components/layout/AppLayout";

export function Settings() {
  return (
    <AppLayout title="Settings">
      <div className="rounded-lg border p-8 text-center">
        <h2 className="text-2xl font-semibold">Settings</h2>
        <p className="mt-2 text-muted-foreground">
          Settings page will be implemented in Phase 4
        </p>
      </div>
    </AppLayout>
  );
}
