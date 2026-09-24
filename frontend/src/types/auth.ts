// Mirrors UserRead (app/auth/schemas.py)
export interface User {
  id: string;
  email: string;
  is_active: boolean;
}

// Mirrors UserCreate — sent when registering
export interface RegisterPayload {
  email: string;
  password: string;
}

// Mirrors Token — returned from POST /auth/login
export interface TokenResponse {
  access_token: string;
  token_type: string;
}
