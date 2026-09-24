import { useQuery } from "@tanstack/react-query"
import { fetchIncidents } from "@/services/incidents"
import type { IncidentFilters } from "@/types/incident"
import type { PaginationParams } from "@/types/api"

export function useIncidents(
  monitorId: string,
  params?: IncidentFilters & PaginationParams,
) {
  return useQuery({
    queryKey: ["incidents", monitorId, params],
    queryFn: () => fetchIncidents(monitorId, params),
    enabled: !!monitorId, // don't run until we actually have a monitor id
    refetchInterval: 5_000,
  });
}
