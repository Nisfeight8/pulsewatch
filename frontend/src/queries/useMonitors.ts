import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createMonitor,
  deleteMonitor,
  fetchMonitor,
  fetchMonitors,
  updateMonitor,
} from "../services/monitors";
import type { MonitorFilters, UpdateMonitorPayload } from "../types/monitor";
import type { PaginationParams } from "@/types/api";

// Reading the list — re-runs automatically whenever `filters` changes,
// because it's part of the queryKey (see explanation below)
export function useMonitors(params?: MonitorFilters & PaginationParams) {
  return useQuery({
    queryKey: ["monitors", params],
    queryFn: () => fetchMonitors(params),
    refetchInterval: 10_000,
  });
}

// Reading a single monitor by id
export function useMonitor(id: string) {
  return useQuery({
    queryKey: ["monitors", id],
    queryFn: () => fetchMonitor(id),
    refetchInterval: 5_000,
  });
}

// Creating a monitor — invalidates the list query on success so it refetches
export function useCreateMonitor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createMonitor,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["monitors"] });
    },
  });
}

export function useUpdateMonitor(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: UpdateMonitorPayload) => updateMonitor(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["monitors"] });
    },
  });
}

export function useDeleteMonitor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteMonitor,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["monitors"] });
    },
  });
}
