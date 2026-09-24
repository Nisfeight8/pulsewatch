import { useState } from "react";
import { Link } from "react-router-dom";
import { useRegister } from "@/queries/useAuth";
import { normalizeError } from "@/services/api-client";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationError, setValidationError] = useState("");

  const registerMutation = useRegister();

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    if (password !== confirmPassword) {
      setValidationError("Passwords do not match");
      return;
    }
    setValidationError("");

    registerMutation.mutate({ email, password });
  }

  if (registerMutation.isSuccess) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <div className="bg-surface-elevated p-8 rounded-xl w-full max-w-sm text-center">
          <h1 className="text-2xl font-bold text-white mb-4">
            Check your email
          </h1>
          <p className="text-gray-300 text-sm">
            We sent a verification link to <strong>{email}</strong>. Click it to
            activate your account, then{" "}
            <Link to="/login" className="text-primary hover:text-primary-hover">
              log in
            </Link>
            .
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface">
      <form
        onSubmit={handleSubmit}
        className="bg-surface-elevated p-8 rounded-xl w-full max-w-sm"
      >
        <h1 className="text-2xl font-bold text-white mb-6">
          Create an account
        </h1>

        <label className="block text-sm text-gray-300 mb-1">Email</label>
        <input
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="w-full px-3 py-2 rounded-lg bg-surface text-white mb-4"
          required
        />

        <label className="block text-sm text-gray-300 mb-1">Password</label>
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="w-full px-3 py-2 rounded-lg bg-surface text-white mb-4"
          required
          minLength={8}
        />

        <label className="block text-sm text-gray-300 mb-1">
          Confirm password
        </label>
        <input
          type="password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          className="w-full px-3 py-2 rounded-lg bg-surface text-white mb-4"
          required
          minLength={8}
        />

        {validationError && (
          <p className="text-danger text-sm mb-4">{validationError}</p>
        )}
        {registerMutation.error && (
          <p className="text-danger text-sm mb-4">
            {normalizeError(registerMutation.error).message}
          </p>
        )}

        <button
          type="submit"
          disabled={registerMutation.isPending}
          className="w-full bg-primary hover:bg-primary-hover text-white py-2 rounded-lg transition-colors disabled:opacity-50"
        >
          {registerMutation.isPending
            ? "Creating account..."
            : "Create account"}
        </button>

        <p className="text-gray-400 text-sm text-center mt-4">
          Already have an account?{" "}
          <Link to="/login" className="text-primary hover:text-primary-hover">
            Log in
          </Link>
        </p>
      </form>
    </div>
  );
}
