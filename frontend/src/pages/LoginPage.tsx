import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLogin } from "../queries/useAuth";
import { normalizeError } from "../services/api-client";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const loginMutation = useLogin();
  const navigate = useNavigate();

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault(); // stop the browser's default full-page form submit

    loginMutation.mutate(
      { email, password },
      {
        onSuccess: () => navigate("/"),
      },
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface">
      <form
        onSubmit={handleSubmit}
        className="bg-surface-elevated p-8 rounded-xl w-full max-w-sm"
      >
        <h1 className="text-2xl font-bold text-white mb-6">Log in</h1>

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
        />

        {loginMutation.error && (
          <p className="text-danger text-sm mb-4">
            {normalizeError(loginMutation.error).message}
          </p>
        )}

        <button
          type="submit"
          disabled={loginMutation.isPending}
          className="w-full bg-primary hover:bg-primary-hover text-white py-2 rounded-lg transition-colors disabled:opacity-50"
        >
          {loginMutation.isPending ? "Logging in..." : "Log in"}
        </button>
      </form>
    </div>
  );
}
