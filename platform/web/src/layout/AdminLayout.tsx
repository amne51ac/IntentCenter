import { NavLink, Outlet } from "react-router-dom";

const LINKS: { to: string; label: string; end: boolean }[] = [
  { to: "/platform/admin/tokens", label: "API tokens", end: true },
  { to: "/platform/admin/identity", label: "Sign-in & identity", end: true },
  { to: "/platform/admin/users", label: "User management", end: true },
  { to: "/platform/admin/audit", label: "Audit log", end: true },
  { to: "/platform/admin/docs", label: "Docs & API", end: true },
  { to: "/platform/admin/health", label: "Service health", end: true },
  { to: "/platform/admin/extensions", label: "Plugins & extensions", end: true },
];

function linkClass(active: boolean) {
  return "admin-subnav-link" + (active ? " admin-subnav-link-active" : "");
}

export function AdminLayout() {
  return (
    <div className="admin-layout">
      <nav className="admin-subnav" aria-label="Administration">
        <p className="admin-subnav-title">Administration</p>
        <ul className="admin-subnav-list">
          {LINKS.map(({ to, label, end }) => (
            <li key={to}>
              <NavLink to={to} end={end} className={({ isActive }) => linkClass(isActive)}>
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <div className="admin-layout-outlet">
        <Outlet />
      </div>
    </div>
  );
}
