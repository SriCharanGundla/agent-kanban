import { useState } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { ApiError, ErrorCode } from "@/lib/errors";

export function LoginForm() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  
  // Get redirect URL from query params (with security validation)
  const rawRedirect = searchParams.get("redirect");
  const redirectTo =
    rawRedirect && rawRedirect.startsWith("/") && !rawRedirect.startsWith("//")
      ? rawRedirect
      : "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>(
    {}
  );

  const validateForm = (): boolean => {
    const newErrors: { email?: string; password?: string } = {};

    // Email validation
    if (!email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Please enter a valid email address";
    }

    // Password validation
    if (!password) {
      newErrors.password = "Password is required";
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
      await login({ email, password });
      toast.success("Welcome back!");
      navigate(redirectTo);
    } catch (error) {
      // Handle ApiError with structured error codes
      if (error instanceof ApiError) {
        switch (error.code) {
          case ErrorCode.INVALID_CREDENTIALS:
            toast.error(error.userMessage);
            setErrors({ password: "Incorrect email or password" });
            return;

          case ErrorCode.USER_INACTIVE:
            toast.error(error.userMessage);
            return;

          case ErrorCode.AUTH_REQUIRED:
          case ErrorCode.INVALID_TOKEN:
          case ErrorCode.TOKEN_EXPIRED:
            toast.error(error.userMessage);
            return;

          default:
            toast.error(error.userMessage);
            return;
        }
      }

      // Fallback for non-ApiError
      toast.error("Failed to log in. Please try again.");
      setErrors({ password: "Invalid email or password" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Field label="Email" invalid={!!errors.email} errorText={errors.email}>
        <Input
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={loading}
          autoComplete="email"
        />
      </Field>

      <Field
        label="Password"
        invalid={!!errors.password}
        errorText={errors.password}
      >
        <Input
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={loading}
          autoComplete="current-password"
        />
      </Field>

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? "Signing in..." : "Sign In"}
      </Button>

      <div className="text-center text-sm text-muted-foreground">
        Don't have an account?{" "}
        <Link
          to="/register"
          className="font-medium text-primary hover:underline"
        >
          Sign up
        </Link>
      </div>
    </form>
  );
}
