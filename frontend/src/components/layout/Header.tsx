import { Link } from "react-router-dom";
import { useAuthStore } from "@/stores/auth-store";
import { useLogout } from "@/queries/useAuth";

export function Header() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const logout = useLogout();

  return (
    <header className="bg-surface-elevated px-8 py-4 flex justify-between items-center">
      <Link to="/" className="text-white font-bold text-lg">
        PulseWatch
      </Link>

      <nav className="flex gap-4 items-center">
        {isAuthenticated ? (
          <>
            <Link to="/" className="text-gray-300 hover:text-white text-sm">
              Monitors
            </Link>
            <button
              onClick={logout}
              className="text-gray-300 hover:text-white text-sm"
            >
              Log out
            </button>
          </>
        ) : (
          <>
            <Link
              to="/login"
              className="text-gray-300 hover:text-white text-sm"
            >
              Login
            </Link>
            <Link
              to="/register"
              className="text-gray-300 hover:text-white text-sm"
            >
              Register
            </Link>
          </>
        )}
      </nav>
    </header>
  );
}
