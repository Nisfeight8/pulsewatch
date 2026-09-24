import { useQuery } from "@tanstack/react-query";
import { fetchIncidents } from "../services/incidents";
import type { IncidentFilters } from "../types/incident";

export function useIncidents(monitorId: string, filters?: IncidentFilters) {
  return useQuery({
    queryKey: ["incidents", monitorId, filters],
    queryFn: () => fetchIncidents(monitorId, filters),
    enabled: !!monitorId, // don't run until we actually have a monitor id
    refetchInterval: 5_000,
  });
}
