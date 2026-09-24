import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getCurrentUser, login, register, verifyEmail } from "../services/auth";
import { useAuthStore } from "../stores/auth-store";
import type { RegisterPayload } from "../types/auth";
import { useEffect } from "react";

export function useCurrentUser() {
  const token = useAuthStore((state) => state.token);

  const query = useQuery({
    queryKey: ["currentUser"],
    queryFn: getCurrentUser,
    enabled: !!token,
  });

  // Keep the store in sync whenever the query has fresh data
  useEffect(() => {
    if (query.data) {
      useAuthStore.getState().setUser(query.data);
    }
  }, [query.data]);

  return query;
}

export function useLogin() {
  const setToken = useAuthStore((state) => state.setToken);

  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      login(email, password),
    onSuccess: (tokenResponse) => {
      setToken(tokenResponse.access_token);
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: (payload: RegisterPayload) => register(payload),
  });
}

export function useLogout() {
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const queryClient = useQueryClient();

  return () => {
    clearAuth();
    queryClient.clear(); // wipe all cached server data — it belonged to the old user
  };
}

export function useVerifyEmail() {
  return useMutation({
    mutationFn: (token: string) => verifyEmail(token),
  });
}
