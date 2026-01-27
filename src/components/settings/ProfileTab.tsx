import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ProfileTab() {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Profile Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm font-medium text-muted-foreground">Full Name</label>
          <p className="mt-1 text-base">{user.full_name}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-muted-foreground">Email</label>
          <p className="mt-1 text-base">{user.email}</p>
        </div>
        <div>
          <label className="text-sm font-medium text-muted-foreground">Account Status</label>
          <p className="mt-1 text-base">
            {user.is_active ? (
              <span className="text-green-600">Active</span>
            ) : (
              <span className="text-destructive">Inactive</span>
            )}
          </p>
        </div>
        <div>
          <label className="text-sm font-medium text-muted-foreground">Member Since</label>
          <p className="mt-1 text-base">
            {new Date(user.created_at).toLocaleDateString()}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
