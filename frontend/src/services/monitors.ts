import { apiClient } from "./api-client";
import type { PaginatedResponse, PaginationParams } from "../types/api";
import type {
  CreateMonitorPayload,
  Monitor,
  MonitorFilters,
  UpdateMonitorPayload,
} from "../types/monitor";

export async function fetchMonitors(
  params?: MonitorFilters & PaginationParams,
): Promise<PaginatedResponse<Monitor>> {
  const response = await apiClient.get<PaginatedResponse<Monitor>>(
    "/monitors",
    {
      params,
    },
  );
  return response.data;
}

export async function fetchMonitor(id: string): Promise<Monitor> {
  const response = await apiClient.get<Monitor>(`/monitors/${id}`);
  return response.data;
}

export async function createMonitor(
  payload: CreateMonitorPayload,
): Promise<Monitor> {
  const response = await apiClient.post<Monitor>("/monitors", payload);
  return response.data;
}

export async function updateMonitor(
  id: string,
  payload: UpdateMonitorPayload,
): Promise<Monitor> {
  const response = await apiClient.patch<Monitor>(`/monitors/${id}`, payload);
  return response.data;
}

export async function deleteMonitor(id: string): Promise<void> {
  await apiClient.delete(`/monitors/${id}`);
}
