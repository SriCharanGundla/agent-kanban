import { LoginForm } from "@/components/auth/LoginForm";

export function Login() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-6 p-6">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold">Welcome Back</h1>
          <p className="text-muted-foreground">Sign in to your account</p>
        </div>
        <div className="rounded-lg border p-6">
          <LoginForm />
        </div>
      </div>
    </div>
  );
}
