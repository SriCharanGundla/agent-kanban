import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { ApiError, ErrorCode } from "@/lib/errors";

export function RegisterForm() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<{
    fullName?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});

  const validateForm = (): boolean => {
    const newErrors: {
      fullName?: string;
      email?: string;
      password?: string;
      confirmPassword?: string;
    } = {};

    // Full name validation
    if (!fullName) {
      newErrors.fullName = "Full name is required";
    } else if (fullName.length < 2) {
      newErrors.fullName = "Full name must be at least 2 characters";
    }

    // Email validation
    if (!email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Please enter a valid email address";
    }

    // Password validation
    if (!password) {
      newErrors.password = "Password is required";
    } else if (password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }

    // Confirm password validation
    if (!confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
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
      await register({
        email,
        password,
        full_name: fullName,
      });
      toast.success("Account created successfully! Logging you in...");
      navigate("/dashboard");
    } catch (error) {
      // Handle ApiError with structured error codes
      if (error instanceof ApiError) {
        switch (error.code) {
          case ErrorCode.REGISTRATION_SUCCESS_LOGIN_FAILED:
            toast.success("Account created successfully!");
            toast.info("Please log in with your new credentials.");
            navigate("/login");
            return;

          case ErrorCode.EMAIL_ALREADY_EXISTS:
            toast.warning(error.userMessage);
            setErrors({ email: "This email is already registered" });
            return;

          case ErrorCode.VALIDATION_ERROR:
            toast.error(error.userMessage);
            return;

          default:
            toast.error(error.userMessage);
            return;
        }
      }

      // Fallback for non-ApiError (shouldn't happen but be defensive)
      toast.error("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Field
        label="Full Name"
        invalid={!!errors.fullName}
        errorText={errors.fullName}
      >
        <Input
          type="text"
          placeholder="John Doe"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          disabled={loading}
          autoComplete="name"
        />
      </Field>

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
          placeholder="Create a strong password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={loading}
          autoComplete="new-password"
        />
      </Field>

      <Field
        label="Confirm Password"
        invalid={!!errors.confirmPassword}
        errorText={errors.confirmPassword}
      >
        <Input
          type="password"
          placeholder="Confirm your password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          disabled={loading}
          autoComplete="new-password"
        />
      </Field>

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? "Creating account..." : "Create Account"}
      </Button>

      <div className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-primary hover:underline">
          Sign in
        </Link>
      </div>
    </form>
  );
}
