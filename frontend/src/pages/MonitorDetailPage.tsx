import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMonitor, useUpdateMonitor } from "@/queries/useMonitors";
import { useIncidents } from "@/queries/useIncidents";
import { useUrlFilters } from "@/hooks/useUrlFilters";
import { normalizeError } from "@/services/api-client";

export default function MonitorDetailPage() {
  // useParams reads the :id from the route path — same idea as
  // Vue Router's route.params.id
  const { id } = useParams<{ id: string }>();

  const { data: monitor, isLoading, error } = useMonitor(id!);
  const updateMutation = useUpdateMonitor(id!);

  const { getParam, getPage, setFilter, setPage } = useUrlFilters();
  const resolvedFilter = getParam("resolved"); // "true" | "false" | ""
  const page = getPage();

  const { data: incidents, isLoading: incidentsLoading } = useIncidents(id!, {
    resolved: resolvedFilter ? resolvedFilter === "true" : undefined,
    page,
    limit: 10,
  });

  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [intervalSeconds, setIntervalSeconds] = useState(60);

  function startEditing() {
    if (!monitor) return;
    setName(monitor.name);
    setUrl(monitor.url);
    setIntervalSeconds(monitor.interval_seconds);
    setIsEditing(true);
  }

  function handleUpdate(event: React.FormEvent) {
    event.preventDefault();
    updateMutation.mutate(
      { name, url, interval_seconds: intervalSeconds },
      { onSuccess: () => setIsEditing(false) },
    );
  }

  if (isLoading) return <p className="text-gray-300 p-8">Loading...</p>;
  if (error)
    return <p className="text-danger p-8">{normalizeError(error).message}</p>;
  if (!monitor) return null;

  return (
    <div className="min-h-screen bg-surface p-8">
      <div className="max-w-2xl mx-auto">
        {/* Monitor details / edit form */}
        <div className="bg-surface-elevated p-6 rounded-xl mb-6">
          {isEditing ? (
            <form onSubmit={handleUpdate} className="space-y-3">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-surface text-white"
                required
              />
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-surface text-white"
                required
              />
              <input
                type="number"
                min={30}
                value={intervalSeconds}
                onChange={(e) => setIntervalSeconds(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-surface text-white"
                required
              />
              {updateMutation.error && (
                <p className="text-danger text-sm">
                  {normalizeError(updateMutation.error).message}
                </p>
              )}
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="bg-primary hover:bg-primary-hover text-white px-4 py-2 rounded-lg disabled:opacity-50"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="text-gray-300 hover:text-white px-4 py-2"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <>
              <div className="flex justify-between items-start">
                <div>
                  <h1 className="text-2xl font-bold text-white">
                    {monitor.name}
                  </h1>
                  <p className="text-gray-400">{monitor.url}</p>
                </div>
                <span
                  className={
                    monitor.last_status === "up"
                      ? "text-success"
                      : monitor.last_status === "down"
                        ? "text-danger"
                        : "text-gray-400"
                  }
                >
                  ● {monitor.last_status}
                </span>
              </div>
              <p className="text-gray-400 text-sm mt-2">
                Checks every {monitor.interval_seconds}s
                {monitor.last_checked_at &&
                  ` — last status change ${new Date(monitor.last_checked_at).toLocaleString()}`}
              </p>
              <button
                onClick={startEditing}
                className="mt-4 text-primary hover:text-primary-hover text-sm"
              >
                Edit
              </button>
            </>
          )}
        </div>

        {/* Incidents */}
        <h2 className="text-xl font-bold text-white mb-3">Incidents</h2>

        <select
          value={resolvedFilter}
          onChange={(e) => setFilter("resolved", e.target.value)}
          className="px-3 py-2 rounded-lg bg-surface-elevated text-white mb-4"
        >
          <option value="">All incidents</option>
          <option value="false">Ongoing</option>
          <option value="true">Resolved</option>
        </select>

        {incidentsLoading && (
          <p className="text-gray-300">Loading incidents...</p>
        )}

        {!incidentsLoading && incidents?.items.length === 0 && (
          <p className="text-gray-400 text-center py-8">No incidents found.</p>
        )}

        <div className="space-y-2 mb-4">
          {incidents?.items.map((incident) => (
            <div
              key={incident.id}
              className="bg-surface-elevated p-4 rounded-xl"
            >
              <div className="flex justify-between text-sm">
                <span
                  className={
                    incident.resolved_at ? "text-success" : "text-danger"
                  }
                >
                  {incident.resolved_at ? "Resolved" : "Ongoing"}
                </span>
                {incident.response_time_ms !== null && (
                  <span className="text-gray-400">
                    {incident.response_time_ms}ms
                  </span>
                )}
              </div>
              <p className="text-gray-300 text-sm mt-1">
                Started {new Date(incident.started_at).toLocaleString()}
              </p>
              {incident.resolved_at && (
                <p className="text-gray-300 text-sm">
                  Resolved {new Date(incident.resolved_at).toLocaleString()}
                </p>
              )}
            </div>
          ))}
        </div>

        {incidents && incidents.total_pages > 1 && (
          <div className="flex justify-between items-center text-gray-300 text-sm">
            <button
              onClick={() => setPage(page - 1)}
              disabled={!incidents.has_previous}
              className="px-3 py-1 rounded-lg bg-surface-elevated disabled:opacity-30"
            >
              Previous
            </button>
            <span>
              Page {incidents.page} of {incidents.total_pages}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={!incidents.has_next}
              className="px-3 py-1 rounded-lg bg-surface-elevated disabled:opacity-30"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
