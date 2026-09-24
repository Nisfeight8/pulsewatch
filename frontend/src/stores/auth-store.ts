import { create } from "zustand";
import type { User } from "../types/auth";

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;

  setToken: (token: string) => void;
  setUser: (user: User) => void;
  clearAuth: () => void;
}

const storedToken = localStorage.getItem("access_token");

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: storedToken,
  isAuthenticated: !!storedToken,

  setToken: (token) => {
    localStorage.setItem("access_token", token);
    set({ token, isAuthenticated: true });
  },

  setUser: (user) => set({ user }),

  clearAuth: () => {
    localStorage.removeItem("access_token");
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
