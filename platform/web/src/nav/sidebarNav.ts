/**
 * Sidebar structure: routes to existing pages, catalog slugs → `/inventory/:slug`,
 * stubs → `/coming-soon/:slug` only when no DB model exists yet.
 */

export type SidebarNavItem =
  | { kind: "route"; label: string; to: string }
  | { kind: "catalog"; label: string; slug: string }
  | { kind: "stub"; label: string; slug: string };

export type SidebarNavSection = { id: string; title: string; items: SidebarNavItem[] };

function sortItemsByLabel(items: SidebarNavItem[]): SidebarNavItem[] {
  return [...items].sort((a, b) => a.label.localeCompare(b.label, "en", { sensitivity: "base" }));
}

const SIDEBAR_NAV_SECTIONS: SidebarNavSection[] = [
  {
    id: "organization",
    title: "Organization",
    items: [
      { kind: "route", label: "Locations", to: "/dcim/locations" },
      { kind: "catalog", label: "Location types", slug: "location-types" },
      { kind: "route", label: "Racks", to: "/dcim/racks" },
      { kind: "catalog", label: "Rack groups", slug: "rack-groups" },
      { kind: "catalog", label: "Rack reservations", slug: "rack-reservations" },
      { kind: "catalog", label: "Elevations", slug: "elevations" },
      { kind: "catalog", label: "Tenants", slug: "tenant" },
      { kind: "catalog", label: "Tenant groups", slug: "tenant-groups" },
      { kind: "catalog", label: "Contacts", slug: "contacts" },
      { kind: "catalog", label: "Teams", slug: "teams" },
      { kind: "catalog", label: "Dynamic groups", slug: "dynamic-groups" },
      { kind: "catalog", label: "Tags", slug: "tags" },
      { kind: "catalog", label: "Custom statuses", slug: "statuses" },
      { kind: "catalog", label: "Device roles", slug: "device-roles" },
      { kind: "catalog", label: "Projects", slug: "projects" },
    ],
  },
  {
    id: "device-types",
    title: "Device types & hardware",
    items: [
      { kind: "catalog", label: "Manufacturers", slug: "manufacturers" },
      { kind: "catalog", label: "Device types", slug: "device-types" },
      { kind: "catalog", label: "Device families", slug: "device-families" },
    ],
  },
  {
    id: "devices",
    title: "Devices & clustering",
    items: [
      { kind: "route", label: "Devices", to: "/dcim/devices" },
      { kind: "catalog", label: "Virtual chassis", slug: "virtual-chassis" },
      { kind: "catalog", label: "Device redundancy groups", slug: "device-redundancy-groups" },
      { kind: "catalog", label: "Interface redundancy groups", slug: "interface-redundancy-groups" },
      { kind: "catalog", label: "Virtual device contexts", slug: "virtual-device-contexts" },
    ],
  },
  {
    id: "device-components",
    title: "Device components",
    items: [
      { kind: "catalog", label: "Interfaces", slug: "interfaces" },
      { kind: "catalog", label: "Front ports", slug: "front-ports" },
      { kind: "catalog", label: "Rear ports", slug: "rear-ports" },
      { kind: "catalog", label: "Console ports", slug: "console-ports" },
      { kind: "catalog", label: "Console server ports", slug: "console-server-ports" },
      { kind: "catalog", label: "Power ports", slug: "power-ports" },
      { kind: "catalog", label: "Power outlets", slug: "power-outlets" },
      { kind: "catalog", label: "Device bays", slug: "device-bays" },
      { kind: "catalog", label: "Module bays", slug: "module-bays" },
      { kind: "catalog", label: "Inventory items", slug: "inventory-items" },
    ],
  },
  {
    id: "modules",
    title: "Modules",
    items: [
      { kind: "catalog", label: "Modules", slug: "modules" },
      { kind: "catalog", label: "Module types", slug: "module-types" },
    ],
  },
  {
    id: "software",
    title: "Software",
    items: [
      { kind: "catalog", label: "Platforms", slug: "platforms" },
      { kind: "catalog", label: "Software versions", slug: "software-versions" },
      { kind: "catalog", label: "Software image files", slug: "software-image-files" },
    ],
  },
  {
    id: "controllers",
    title: "Controllers & automation",
    items: [
      { kind: "catalog", label: "Controllers", slug: "controllers" },
      { kind: "catalog", label: "Device groups", slug: "device-groups" },
    ],
  },
  {
    id: "connections",
    title: "Connections",
    items: [
      { kind: "catalog", label: "Cables", slug: "cables" },
      { kind: "catalog", label: "Console connections", slug: "console-connections" },
      { kind: "catalog", label: "Power connections", slug: "power-connections" },
    ],
  },
  {
    id: "ipam",
    title: "IPAM",
    items: [
      { kind: "catalog", label: "Namespaces", slug: "namespaces" },
      { kind: "route", label: "VRFs", to: "/ipam/vrfs" },
      { kind: "catalog", label: "Route targets", slug: "route-targets" },
      { kind: "route", label: "Prefixes", to: "/ipam/prefixes" },
      { kind: "route", label: "IP addresses", to: "/ipam/ip-addresses" },
      { kind: "catalog", label: "RIRs", slug: "rirs" },
      { kind: "catalog", label: "VLAN groups", slug: "vlan-groups" },
      { kind: "route", label: "VLANs", to: "/ipam/vlans" },
      { kind: "route", label: "Services", to: "/platform/services" },
    ],
  },
  {
    id: "circuits",
    title: "Circuits",
    items: [
      { kind: "route", label: "Providers", to: "/circuits/providers" },
      { kind: "catalog", label: "Provider networks", slug: "provider-networks" },
      { kind: "catalog", label: "Circuit types", slug: "circuit-types" },
      { kind: "catalog", label: "Circuit diversity groups", slug: "circuit-diversity-groups" },
      { kind: "route", label: "Circuits", to: "/circuits/circuits" },
      { kind: "catalog", label: "Circuit terminations", slug: "circuit-terminations" },
      { kind: "catalog", label: "Circuit segments", slug: "circuit-segments" },
    ],
  },
  {
    id: "membership",
    title: "Membership & links",
    items: [
      { kind: "catalog", label: "Virtual chassis members", slug: "virtual-chassis-members" },
      { kind: "catalog", label: "Device redundancy members", slug: "device-redundancy-group-members" },
      { kind: "catalog", label: "Interface redundancy members", slug: "interface-redundancy-group-members" },
    ],
  },
  {
    id: "inventory-extended",
    title: "Cloud, wireless & compute",
    items: [
      { kind: "catalog", label: "Power panels", slug: "power-panels" },
      { kind: "catalog", label: "Power feeds", slug: "power-feeds" },
      { kind: "catalog", label: "Cloud networks", slug: "cloud-networks" },
      { kind: "catalog", label: "Cloud services", slug: "cloud-services" },
      { kind: "catalog", label: "Wireless networks", slug: "wireless-networks" },
      { kind: "catalog", label: "VPNs", slug: "vpns" },
      { kind: "catalog", label: "Clusters", slug: "clusters" },
      { kind: "catalog", label: "Virtual machines", slug: "virtual-machines" },
      { kind: "catalog", label: "MPLS domains", slug: "mpls" },
      { kind: "catalog", label: "Service instances", slug: "service-instances" },
    ],
  },
  {
    id: "platform",
    title: "Platform",
    items: [
      { kind: "route", label: "Jobs", to: "/platform/jobs" },
      { kind: "route", label: "Job runs", to: "/platform/job-runs" },
      { kind: "route", label: "Audit log", to: "/platform/audit" },
      { kind: "route", label: "Object templates", to: "/platform/object-templates" },
    ],
  },
];

/** Sections and routes; items within each section are alphabetical by label (nav + overview). */
export const SIDEBAR_NAV: SidebarNavSection[] = SIDEBAR_NAV_SECTIONS.map((section) => ({
  ...section,
  items: sortItemsByLabel(section.items),
}));

export function navItemToPath(item: SidebarNavItem): string {
  if (item.kind === "route") return item.to;
  if (item.kind === "catalog") return `/inventory/${item.slug}`;
  return `/coming-soon/${item.slug}`;
}
