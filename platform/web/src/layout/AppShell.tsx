import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { apiJson, logout } from "../api/client";
import { CollapsibleNavSection } from "../components/CollapsibleNavSection";
import { GlobalSearch } from "../components/GlobalSearch";
import { SIDEBAR_NAV, navItemToPath, type SidebarNavItem } from "../nav/sidebarNav";

function SidebarNavLink({ item }: { item: SidebarNavItem }) {
  const to = navItemToPath(item);
  return (
    <NavLink
      to={to}
      className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
      title={item.kind === "stub" ? "Planned — not in schema yet" : undefined}
    >
      {item.label}
    </NavLink>
  );
}

type PinnedPage = { path: string; label: string };

type Me = {
  preferences?: { pinnedPages?: PinnedPage[] };
  auth: { mode: "user" } | { mode: "api_token" };
};

export function AppShell() {
  const navigate = useNavigate();
  const qc = useQueryClient();

  const me = useQuery({
    queryKey: ["me"],
    queryFn: () => apiJson<Me>("/v1/me"),
  });

  const patchPrefs = useMutation({
    mutationFn: (preferences: Record<string, unknown>) =>
      apiJson("/v1/me", { method: "PATCH", body: JSON.stringify({ preferences }) }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["me"] });
    },
  });

  const isUser = me.data?.auth?.mode === "user";
  const pinned = (me.data?.preferences?.pinnedPages ?? []) as PinnedPage[];

  function unpinOne(path: string) {
    if (!isUser) return;
    patchPrefs.mutate({ pinnedPages: pinned.filter((p) => p.path !== path) });
  }

  async function signOut() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-root">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>IntentCenter</h1>
          <p>Network intent & inventory — operator console</p>
        </div>

        {isUser && pinned.length > 0 ? (
          <div className="nav-section pinned-pages-section pinned-pages-top">
            <div className="nav-section-title">Pinned pages</div>
            {pinned.map((p) => (
              <div key={p.path} className="pinned-page-row">
                <NavLink
                  to={p.path}
                  className={({ isActive }) => "nav-link pinned-nav-link" + (isActive ? " active" : "")}
                  title={p.path}
                >
                  {p.label}
                </NavLink>
                <button
                  type="button"
                  className="btn-unpin"
                  onClick={() => unpinOne(p.path)}
                  aria-label={`Unpin ${p.label}`}
                  disabled={patchPrefs.isPending}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        ) : null}

        <div className="sidebar-search-wrap">
          <GlobalSearch />
        </div>

        <nav className="sidebar-nav-scroll">
          <div className="nav-section">
            <NavLink to="/" end className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}>
              Overview
            </NavLink>
          </div>
          {SIDEBAR_NAV.map((section) => (
            <CollapsibleNavSection key={section.id} id={section.id} title={section.title}>
              {section.items.map((item) => (
                <SidebarNavLink key={`${section.id}-${navItemToPath(item)}-${item.label}`} item={item} />
              ))}
            </CollapsibleNavSection>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button type="button" className="btn btn-ghost" onClick={() => void signOut()}>
            Sign out
          </button>
        </div>
      </aside>
      <div className="main">
        <Outlet />
      </div>
    </div>
  );
}
