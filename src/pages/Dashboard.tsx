import { AppLayout } from "@/components/layout/AppLayout";

export function Dashboard() {
  return (
    <AppLayout title="Dashboard">
      <div className="rounded-lg border p-8 text-center">
        <h2 className="text-2xl font-semibold">Dashboard</h2>
        <p className="mt-2 text-muted-foreground">
          Dashboard content will be implemented in Phase 4
        </p>
      </div>
    </AppLayout>
  );
}
