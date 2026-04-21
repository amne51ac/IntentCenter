import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiJson } from "../api/client";
import { ModelListPageHeader } from "../components/ModelListPageHeader";
import { navItemToPath, SIDEBAR_NAV, type SidebarNavItem } from "../nav/sidebarNav";
import { catalogBySlug } from "./inventory/inventoryCatalogConfig";
import { BlockLoader, InlineLoader, Spinner } from "../components/Loader";

type Me = {
  organization: { id: string; name: string; slug: string };
  auth:
    | {
        mode: "user";
        user: {
          id: string;
          email: string;
          displayName: string | null;
          role: string;
          authProvider: string;
        };
      }
    | {
        mode: "api_token";
        token: { id: string; name: string; role: string };
      };
};

/** List endpoints that return `{ items: [...] }` for row counts on the overview. */
const ROUTE_LIST_API: Partial<Record<string, string>> = {
  "/dcim/locations": "/v1/locations",
  "/dcim/racks": "/v1/racks",
  "/dcim/devices": "/v1/devices",
  "/ipam/vrfs": "/v1/vrfs",
  "/ipam/prefixes": "/v1/prefixes",
  "/ipam/ip-addresses": "/v1/ip-addresses",
  "/ipam/vlans": "/v1/vlans",
  "/circuits/providers": "/v1/providers",
  "/circuits/circuits": "/v1/circuits",
  "/platform/services": "/v1/services",
  "/platform/jobs": "/v1/jobs",
  "/platform/job-runs": "/v1/job-runs",
  "/platform/audit": "/v1/audit-events?limit=100",
  "/platform/object-templates": "/v1/templates",
};

async function countList(path: string): Promise<number> {
  const data = await apiJson<{ items: unknown[] }>(path);
  return data.items.length;
}

function countKey(sectionId: string, itemIndex: number): string {
  return `${sectionId}:${itemIndex}`;
}

async function fetchCountForItem(item: SidebarNavItem): Promise<number | null> {
  try {
    if (item.kind === "stub") return null;
    if (item.kind === "route") {
      const api = ROUTE_LIST_API[item.to];
      if (!api) return null;
      return await countList(api);
    }
    if (item.kind === "catalog") {
      const def = catalogBySlug(item.slug);
      if (!def) return null;
      return await countList(`/v1/catalog/${encodeURIComponent(def.apiType)}/items`);
    }
  } catch {
    return null;
  }
  return null;
}

async function fetchOverviewCounts(): Promise<Record<string, number | null>> {
  const tasks: Promise<[string, number | null]>[] = [];
  for (const section of SIDEBAR_NAV) {
    section.items.forEach((item, itemIndex) => {
      const key = countKey(section.id, itemIndex);
      tasks.push(
        fetchCountForItem(item).then((count) => [key, count] as [string, number | null]),
      );
    });
  }
  const rows = await Promise.all(tasks);
  return Object.fromEntries(rows);
}

export function Dashboard() {
  const me = useQuery({
    queryKey: ["me"],
    queryFn: () => apiJson<Me>("/v1/me"),
  });

  const counts = useQuery({
    queryKey: ["dashboard-overview-counts"],
    queryFn: fetchOverviewCounts,
  });

  if (me.isLoading) {
    return (
      <>
        <ModelListPageHeader title="Overview" showBulkTools={false} />
        <div className="main-body">
          <BlockLoader label="Loading overview…" />
        </div>
      </>
    );
  }

  if (me.error) {
    return (
      <>
        <ModelListPageHeader title="Overview" showBulkTools={false} />
        <div className="main-body error-banner">{String(me.error)}</div>
      </>
    );
  }

  const m = me.data!;
  const role = m.auth.mode === "user" ? m.auth.user.role : m.auth.token.role;
  const label =
    m.auth.mode === "user"
      ? m.auth.user.displayName || m.auth.user.email
      : `API token · ${m.auth.token.name}`;

  const c = counts.data;

  return (
    <>
      <ModelListPageHeader
        title="Overview"
        subtitle="Jump to any inventory list, or use the sidebar. Counts update from each list API."
        showBulkTools={false}
      />
      <div className="main-body overview-page">
        <div className="context-strip">
          <div className="context-strip-cluster">
            <p className="context-strip-heading">Signed in</p>
            <p className="context-strip-body">
              <span className="mono">{label}</span>{" "}
              <span className={"badge " + (role === "ADMIN" ? "badge-admin" : "")}>{role}</span>
              {m.auth.mode === "user" ? (
                <span className="muted"> · {m.auth.user.authProvider}</span>
              ) : null}
            </p>
          </div>
          <div className="context-strip-cluster">
            <p className="context-strip-heading">Organization</p>
            <p className="context-strip-body">
              <strong>{m.organization.name}</strong>{" "}
              <span className="mono badge">{m.organization.slug}</span>
            </p>
          </div>
        </div>

        <p className="page-lede muted">
          Each row below is a list in this console. Numbers are row counts from the corresponding API (audit shows a recent sample, max 100).
        </p>

        {counts.isLoading ? <InlineLoader label="Loading object counts…" /> : null}
        {counts.error ? <div className="error-banner">{String(counts.error)}</div> : null}

        <div className="overview-categories">
          {SIDEBAR_NAV.map((section) => (
            <section key={section.id} className="overview-category">
              <h3 className="overview-category-title">{section.title}</h3>
              <ul className="overview-type-list">
                {section.items.map((item, itemIndex) => {
                  const to = navItemToPath(item);
                  const kindClass =
                    item.kind === "stub" ? "overview-type-kind overview-type-kind-stub" : "overview-type-kind overview-type-kind-live";
                  const countVal = c ? c[countKey(section.id, itemIndex)] : null;
                  const countDisplay =
                    item.kind === "stub"
                      ? "—"
                      : countVal === null || countVal === undefined
                        ? "—"
                        : String(countVal);
                  const countTitle =
                    item.kind === "stub"
                      ? "Not modeled yet — roadmap page"
                      : item.kind === "route" && item.to === "/platform/audit"
                        ? "Recent audit events in sample (max 100)"
                        : "Rows in current list";

                  return (
                    <li key={`${section.id}-${itemIndex}`} className="overview-type-row">
                      <Link to={to} className="overview-type-link">
                        {item.label}
                      </Link>
                      <span className={kindClass} title={item.kind === "stub" ? "Planned" : item.kind}>
                        {item.kind === "catalog" ? "Catalog" : item.kind === "route" ? "List" : "Planned"}
                      </span>
                      <span className="overview-type-count mono" title={countTitle}>
                        {counts.isLoading ? <Spinner size="sm" /> : countDisplay}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </div>

        <p className="muted" style={{ marginBottom: 0 }}>
          REST API: <code className="mono">/v1/…</code> · OpenAPI: <a href="/docs">/docs</a> · GraphQL:{" "}
          <a href="/graphql">/graphql</a> · GraphiQL: <a href="/graphiql">/graphiql</a>
        </p>
      </div>
    </>
  );
}
