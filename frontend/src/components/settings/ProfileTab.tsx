import { useState } from "react";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";

export function ProfileTab() {
  const { user, updateProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ fullName?: string }>({});

  if (!user) {
    return null;
  }

  const handleEdit = () => {
    setFullName(user.full_name);
    setErrors({});
    setIsEditing(true);
  };

  const handleCancel = () => {
    setFullName(user.full_name);
    setErrors({});
    setIsEditing(false);
  };

  const handleSave = async () => {
    // Validate
    const newErrors: { fullName?: string } = {};
    if (!fullName.trim()) {
      newErrors.fullName = "Full name is required";
    } else if (fullName.trim().length < 2) {
      newErrors.fullName = "Full name must be at least 2 characters";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setLoading(true);
    try {
      await updateProfile({ full_name: fullName.trim() });
      toast.success("Profile updated successfully");
      setIsEditing(false);
      setErrors({});
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to update profile";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Profile Information</CardTitle>
          {!isEditing && (
            <Button onClick={handleEdit} variant="outline" size="sm">
              Edit Profile
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm font-medium text-muted-foreground">Full Name</label>
          {isEditing ? (
            <Field invalid={!!errors.fullName} errorText={errors.fullName}>
              <Input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                disabled={loading}
                placeholder="Enter your full name"
              />
            </Field>
          ) : (
            <p className="mt-1 text-base">{user.full_name}</p>
          )}
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

        {isEditing && (
          <div className="flex gap-2 pt-2">
            <Button onClick={handleSave} disabled={loading}>
              {loading ? "Saving..." : "Save Changes"}
            </Button>
            <Button onClick={handleCancel} variant="outline" disabled={loading}>
              Cancel
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
