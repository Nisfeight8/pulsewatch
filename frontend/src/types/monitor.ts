// Mirrors MonitorStatus (app/monitor/models.py)
export type MonitorStatus = "up" | "down" | "unknown";

// Mirrors MonitorRead (app/monitor/schemas.py)
export interface Monitor {
  id: string;
  name: string;
  url: string;
  interval_seconds: number;
  is_active: boolean;
  last_status: MonitorStatus;
  last_checked_at: string | null;
  created_at: string;
}

// Mirrors MonitorCreate
export interface CreateMonitorPayload {
  name: string;
  url: string;
  interval_seconds?: number;
}

// Mirrors MonitorUpdate — every field optional, matches PATCH semantics
export interface UpdateMonitorPayload {
  name?: string;
  url?: string;
  interval_seconds?: number;
  is_active?: boolean;
}

// Mirrors MonitorFilters — used as query params on GET /monitors
export interface MonitorFilters {
  is_active?: boolean;
  status?: MonitorStatus;
  search?: string;
}
