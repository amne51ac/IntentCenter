import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiJson } from "../api/client";
import { InlineLoader } from "./Loader";

type Hit = {
  resourceType: string;
  id: string;
  label: string;
  path: string;
  subtitle?: string;
};

export function GlobalSearch() {
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  useEffect(() => {
    const t = window.setTimeout(() => setDebounced(q.trim()), 200);
    return () => window.clearTimeout(t);
  }, [q]);

  const search = useQuery({
    queryKey: ["search", debounced],
    queryFn: () => apiJson<{ items: Hit[] }>(`/v1/search?q=${encodeURIComponent(debounced)}&limit=20`),
    enabled: debounced.length >= 2,
  });

  const panelOpen = debounced.length >= 2;

  return (
    <div className="global-search">
      <input
        type="search"
        className="input global-search-input"
        placeholder="Search inventory…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        aria-label="Global search"
        autoComplete="off"
      />
      {panelOpen ? (
        <div className="global-search-results" role="listbox">
          {search.isLoading ? (
            <div className="global-search-loading">
              <InlineLoader label="Searching…" />
            </div>
          ) : null}
          {!search.isLoading && search.error ? (
            <div className="global-search-empty error-banner" style={{ margin: 0 }}>
              {String(search.error)}
            </div>
          ) : null}
          {!search.isLoading && !search.error && (search.data?.items.length ?? 0) === 0 ? (
            <div className="global-search-empty muted">No results</div>
          ) : null}
          {!search.isLoading &&
            !search.error &&
            search.data?.items.map((h) => (
              <Link key={`${h.resourceType}-${h.id}`} to={h.path} className="global-search-hit" role="option" onClick={() => setQ("")}>
                <span className="global-search-hit-type">{h.resourceType}</span>
                <span className="global-search-hit-label">{h.label}</span>
                {h.subtitle ? <span className="global-search-hit-sub muted">{h.subtitle}</span> : null}
              </Link>
            ))}
        </div>
      ) : null}
    </div>
  );
}
