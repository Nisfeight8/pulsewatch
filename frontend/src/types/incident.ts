// Mirrors IncidentRead (app/incident/schemas.py)
export interface Incident {
  id: string;
  monitor_id: string;
  started_at: string;
  resolved_at: string | null;
  response_time_ms: number | null;
}

// Mirrors IncidentFilters
export interface IncidentFilters {
  resolved?: boolean;
  started_after?: string;
  started_before?: string;
}
