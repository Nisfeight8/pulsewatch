import axios, { type AxiosError } from "axios";
import type { ApiError, ValidationErrorDetail } from "../types/api";

// Base URL comes from Vite's env system — set VITE_API_URL in .env
// (Vite only exposes env vars prefixed with VITE_ to client code)
const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Runs before every request — attaches the JWT token if we have one.
// This is the axios "interceptor" concept: middleware for requests/responses.
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// A normalized error shape our app code will always deal with,
// regardless of whether the backend sent a plain HTTPException detail
// or a Pydantic validation error array.
export interface NormalizedError {
  message: string;
  status: number | null;
}

// Type guard: narrows ApiError to the validation-error shape specifically.
// TypeScript uses the return type "data is ValidationErrorDetail" to know
// that inside an `if` using this function, `data` is safely that type.
function isValidationError(data: ApiError): data is ValidationErrorDetail {
  return Array.isArray(data.detail);
}

// Converts any axios error into our NormalizedError shape.
// Call this in a catch block wherever you make an API call.
export function normalizeError(error: unknown): NormalizedError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>;
    const data = axiosError.response?.data;

    if (data) {
      if (isValidationError(data)) {
        // Join multiple validation messages into one readable string
        const message = data.detail.map((item) => item.msg).join(", ");
        return { message, status: axiosError.response?.status ?? null };
      }
      return {
        message: data.detail,
        status: axiosError.response?.status ?? null,
      };
    }

    // Request was made but no response came back (network error, CORS, etc)
    return {
      message: "Network error — please check your connection",
      status: null,
    };
  }

  // Not even an axios error — something unexpected happened
  return { message: "An unexpected error occurred", status: null };
}
