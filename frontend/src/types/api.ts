// Mirrors PaginationParams (app/shared/pagination.py) — sent as query params
export interface PaginationParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: "asc" | "desc";
}

// Mirrors the API's PaginatedResponse[T] shape (app/shared/pagination.py)
export interface PaginatedResponse<T> {
  total: number;
  page: number;
  limit: number;
  items: T[];
  has_next: boolean;
  has_previous: boolean;
  total_pages: number;
}

// FastAPI's default error shape for a raised HTTPException:
// { "detail": "some message" }
export interface ApiErrorDetail {
  detail: string;
}

// FastAPI's error shape for Pydantic validation failures (422 responses):
// { "detail": [{ "loc": [...], "msg": "...", "type": "..." }] }
export interface ValidationErrorItem {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ValidationErrorDetail {
  detail: ValidationErrorItem[];
}

// A single type that covers both shapes, so calling code can check
// which one it actually got with a type guard (see api-client.ts next)
export type ApiError = ApiErrorDetail | ValidationErrorDetail;
