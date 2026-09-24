import { useSearchParams } from "react-router-dom";

// A generic, reusable hook for syncing filter/pagination state with the URL.
// Works for any set of string-based filter keys — DashboardPage uses it for
// monitors (search, status), MonitorDetailPage will use it for incidents (resolved).
export function useUrlFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  function getParam(key: string): string {
    return searchParams.get(key) ?? "";
  }

  function getPage(): number {
    return Number(searchParams.get("page") ?? "1");
  }

  // Sets one filter param, always resetting page back to 1 —
  // changing a filter should never leave you stranded on a stale page
  function setFilter(key: string, value: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) next.set(key, value);
      else next.delete(key);
      next.set("page", "1");
      return next;
    });
  }

  function setPage(page: number) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("page", String(page));
      return next;
    });
  }

  return { getParam, getPage, setFilter, setPage };
}
