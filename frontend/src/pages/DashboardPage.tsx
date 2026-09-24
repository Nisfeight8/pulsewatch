import { useState } from "react";
import { Link } from "react-router-dom";
import {
  useCreateMonitor,
  useDeleteMonitor,
  useMonitors,
} from "@/queries/useMonitors";
import { normalizeError } from "@/services/api-client";
import type { MonitorStatus } from "@/types/monitor";
import { useUrlFilters } from "@/hooks/useUrlFilters";

export default function DashboardPage() {
  const { getParam, getPage, setFilter, setPage } = useUrlFilters();
  const search = getParam("search");
  const statusFilter = getParam("status") as MonitorStatus | "";
  const page = getPage();

  const { data, isLoading, error } = useMonitors({
    search: search || undefined,
    status: statusFilter || undefined,
    page,
    limit: 5,
  });

  const createMutation = useCreateMonitor();
  const deleteMutation = useDeleteMonitor();

  const [name, setName] = useState("");
  const [url, setUrl] = useState("");

  function handleCreate(event: React.SubmitEvent) {
    event.preventDefault();
    createMutation.mutate(
      { name, url },
      {
        onSuccess: () => {
          setName("");
          setUrl("");
        },
      },
    );
  }

  return (
    <div className="min-h-screen bg-surface p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-white mb-6">Monitors</h1>

        {/* Create form */}
        <form
          onSubmit={handleCreate}
          className="bg-surface-elevated p-4 rounded-xl mb-6 flex gap-2"
        >
          <input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1 px-3 py-2 rounded-lg bg-surface text-white"
            required
          />
          <input
            type="url"
            placeholder="https://example.com"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="flex-1 px-3 py-2 rounded-lg bg-surface text-white"
            required
          />
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="bg-primary hover:bg-primary-hover text-white px-4 py-2 rounded-lg disabled:opacity-50"
          >
            Add
          </button>
        </form>
        {createMutation.error && (
          <p className="text-danger text-sm mb-4">
            {normalizeError(createMutation.error).message}
          </p>
        )}

        {/* Search + status filter */}
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="Search by name..."
            value={search}
            onChange={(e) => setFilter("search", e.target.value)}
            className="flex-1 px-3 py-2 rounded-lg bg-surface-elevated text-white"
          />
          <select
            value={statusFilter}
            onChange={(e) => setFilter("status", e.target.value)}
            className="px-3 py-2 rounded-lg bg-surface-elevated text-white"
          >
            <option value="">All statuses</option>
            <option value="up">Up</option>
            <option value="down">Down</option>
            <option value="unknown">Unknown</option>
          </select>
        </div>

        {!isLoading && !error && data?.items.length === 0 && (
          <p className="text-gray-400 text-center py-8">
            {search || statusFilter
              ? "No monitors match your filters."
              : "No monitors yet — add your first one above."}
          </p>
        )}

        {isLoading && <p className="text-gray-300">Loading...</p>}
        {error && (
          <p className="text-danger">{normalizeError(error).message}</p>
        )}

        <div className="space-y-2 mb-4">
          {data?.items.map((monitor) => (
            <div
              key={monitor.id}
              className="bg-surface-elevated p-4 rounded-xl flex justify-between items-center"
            >
              <Link
                to={`/monitors/${monitor.id}`}
                className="text-white hover:text-primary"
              >
                <span
                  className={
                    monitor.last_status === "up"
                      ? "text-success"
                      : monitor.last_status === "down"
                        ? "text-danger"
                        : "text-gray-400"
                  }
                >
                  ●
                </span>{" "}
                {monitor.name}
                <span className="text-gray-400 text-sm ml-2">
                  {monitor.url}
                </span>
              </Link>
              <button
                onClick={() => deleteMutation.mutate(monitor.id)}
                className="text-danger hover:text-red-400 text-sm cursor-pointer"
              >
                Delete
              </button>
            </div>
          ))}
        </div>

        {/* Pagination controls */}
        {data && data.total_pages > 1 && (
          <div className="flex justify-between items-center text-gray-300 text-sm">
            <button
              onClick={() => setPage(page - 1)}
              disabled={!data.has_previous}
              className="px-3 py-1 rounded-lg bg-surface-elevated disabled:opacity-30"
            >
              Previous
            </button>
            <span>
              Page {data.page} of {data.total_pages}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={!data.has_next}
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
