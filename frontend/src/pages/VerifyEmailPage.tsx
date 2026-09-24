import { useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useVerifyEmail } from "@/queries/useAuth";
import { normalizeError } from "@/services/api-client";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const verifyMutation = useVerifyEmail();

  // Run the verification exactly once, as soon as we have a token —
  // this is a side-effect triggered by data (the token), not by a click,
  // so it goes in useEffect rather than an onClick handler.
  useEffect(() => {
    if (token) {
      verifyMutation.mutate(token);
    }
  }, [token]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface">
      <div className="bg-surface-elevated p-8 rounded-xl w-full max-w-sm text-center">
        {!token && (
          <p className="text-danger">
            No verification token found in the link.
          </p>
        )}

        {token && verifyMutation.isPending && (
          <p className="text-gray-300">Verifying your email...</p>
        )}

        {token && verifyMutation.isSuccess && (
          <>
            <h1 className="text-2xl font-bold text-white mb-4">
              Email verified!
            </h1>
            <Link to="/login" className="text-primary hover:text-primary-hover">
              Go to login
            </Link>
          </>
        )}

        {token && verifyMutation.isError && (
          <p className="text-danger">
            {normalizeError(verifyMutation.error).message}
          </p>
        )}
      </div>
    </div>
  );
}
