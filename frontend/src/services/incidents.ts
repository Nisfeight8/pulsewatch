import { apiClient } from "./api-client";
import type { PaginatedResponse } from "../types/api";
import type { Incident, IncidentFilters } from "../types/incident";

export async function fetchIncidents(
  monitorId: string,
  filters?: IncidentFilters,
): Promise<PaginatedResponse<Incident>> {
  const response = await apiClient.get<PaginatedResponse<Incident>>(
    `/monitors/${monitorId}/incidents`,
    { params: filters },
  );
  return response.data;
}
