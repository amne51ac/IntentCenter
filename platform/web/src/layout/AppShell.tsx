import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { apiJson } from "../api/client";
import { CollapsibleNavSection } from "../components/CollapsibleNavSection";
import { GlobalSearch } from "../components/GlobalSearch";
import { SidebarUserMenu } from "../components/SidebarUserMenu";
import { publicAssetUrl } from "../lib/publicAssetUrl";
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
  auth:
    | { mode: "user"; user: { role: string; email: string; displayName: string | null } }
    | { mode: "api_token"; token: { role: string; name: string } };
};

export function AppShell() {
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

  const [openNavSectionId, setOpenNavSectionId] = useState<string | null>(null);

  const isUser = me.data?.auth?.mode === "user";
  const isAdmin =
    me.data?.auth?.mode === "user"
      ? me.data.auth.user.role === "ADMIN"
      : me.data?.auth?.mode === "api_token" && me.data.auth.token.role === "ADMIN";
  const pinned = (me.data?.preferences?.pinnedPages ?? []) as PinnedPage[];

  function unpinOne(path: string) {
    if (!isUser) return;
    patchPrefs.mutate({ pinnedPages: pinned.filter((p) => p.path !== path) });
  }

  return (
    <div className="app-root">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <NavLink to="/" end className="sidebar-brand-link" title="IntentCenter — Overview">
            <img
              src={publicAssetUrl("intentcenter-logo.svg")}
              alt="IntentCenter"
              className="sidebar-wordmark"
              width={420}
              height={84}
            />
          </NavLink>
          <p className="brand-tagline">Network source of truth — intent & inventory</p>
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
          <div className="nav-section" data-nav-section="overview">
            <NavLink
              to="/"
              end
              className={({ isActive }) => "nav-link" + (isActive ? " active" : "")}
              title="Overview"
            >
              Overview
            </NavLink>
          </div>
          {SIDEBAR_NAV.map((section) => (
            <CollapsibleNavSection
              key={section.id}
              id={section.id}
              title={section.title}
              open={openNavSectionId === section.id}
              onToggle={() => {
                setOpenNavSectionId((cur) => (cur === section.id ? null : section.id));
              }}
            >
              {section.items
                .filter((item) => (item.kind === "route" && item.adminOnly ? isAdmin : true))
                .map((item) => (
                  <SidebarNavLink key={`${section.id}-${navItemToPath(item)}-${item.label}`} item={item} />
                ))}
            </CollapsibleNavSection>
          ))}
        </nav>

        <div className="sidebar-footer">
          <SidebarUserMenu me={me.data} />
        </div>
      </aside>
      <div className="main">
        <Outlet />
      </div>
    </div>
  );
}
