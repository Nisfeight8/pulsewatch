import { apiClient } from "./api-client";
import type { RegisterPayload, TokenResponse, User } from "../types/auth";

// POST /auth/register — creates a new account, triggers a verification email
export async function register(payload: RegisterPayload): Promise<User> {
  const response = await apiClient.post<User>("/auth/register", payload);
  return response.data;
}

// POST /auth/login — the API expects form-encoded data (OAuth2PasswordRequestForm),
// not JSON, so we build a URLSearchParams body instead of a plain object
export async function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  const body = new URLSearchParams();
  body.set("username", email); // the backend's OAuth2 form field is called "username"
  body.set("password", password);

  const response = await apiClient.post<TokenResponse>("/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return response.data;
}

// GET /auth/me — returns the currently authenticated user (requires a valid token)
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");
  return response.data;
}

// POST /auth/resend-verification
export async function resendVerification(email: string): Promise<void> {
  await apiClient.post("/auth/resend-verification", { email });
}

// GET /auth/verify-email?token=...
export async function verifyEmail(token: string): Promise<void> {
  await apiClient.get("/auth/verify-email", { params: { token } });
}
