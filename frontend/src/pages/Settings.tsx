import { AppLayout } from "@/components/layout/AppLayout";
import { ProfileTab } from "@/components/settings/ProfileTab";
import { ApiKeysTab } from "@/components/settings/ApiKeysTab";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function Settings() {
  return (
    <AppLayout title="Settings">
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold">Settings</h2>
          <p className="text-muted-foreground">
            Manage your account settings and API keys
          </p>
        </div>

        <Tabs defaultValue="profile" className="w-full">
          <TabsList>
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="api-keys">API Keys</TabsTrigger>
          </TabsList>

          <TabsContent value="profile" className="mt-6">
            <ProfileTab />
          </TabsContent>

          <TabsContent value="api-keys" className="mt-6">
            <ApiKeysTab />
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
}
