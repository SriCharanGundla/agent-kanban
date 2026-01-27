import { RegisterForm } from "@/components/auth/RegisterForm";

export function Register() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-6 p-6">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold">Create an Account</h1>
          <p className="text-muted-foreground">Get started with AgentKanban</p>
        </div>
        <div className="rounded-lg border p-6">
          <RegisterForm />
        </div>
      </div>
    </div>
  );
}
