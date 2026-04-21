/** Slug in URL → API catalog / bulk resource type (`/v1/catalog/{apiType}/items`) */
export type CatalogPageDef = {
  slug: string;
  apiType: string;
  title: string;
  subtitle: string;
  /** Lowercase noun phrase for actions, e.g. "Add {addNoun}" — matches other list pages (Add device, Add prefix). */
  addNoun: string;
};

/** Every `kind: "catalog"` entry in `nav/sidebarNav.ts` must appear here. */
export const INVENTORY_CATALOG: CatalogPageDef[] = [
  { slug: "tenant", apiType: "Tenant", title: "Tenants", subtitle: "Current organization (tenant scope for all inventory)", addNoun: "tenant" },
  { slug: "location-types", apiType: "LocationType", title: "Location types", subtitle: "Site / facility taxonomy (global)", addNoun: "location type" },
  { slug: "manufacturers", apiType: "Manufacturer", title: "Manufacturers", subtitle: "Hardware vendors (global)", addNoun: "manufacturer" },
  { slug: "device-types", apiType: "DeviceType", title: "Device types", subtitle: "Manufacturer models (global catalog)", addNoun: "device type" },
  { slug: "device-families", apiType: "DeviceFamily", title: "Device families", subtitle: "Product lines / families (global)", addNoun: "device family" },
  { slug: "device-roles", apiType: "DeviceRole", title: "Device roles", subtitle: "Router, switch, server, … (global)", addNoun: "device role" },
  { slug: "projects", apiType: "Project", title: "Projects", subtitle: "Scoped work or customer projects", addNoun: "project" },
  { slug: "dynamic-groups", apiType: "DynamicGroup", title: "Dynamic groups", subtitle: "Saved filters and membership rules", addNoun: "dynamic group" },
  { slug: "tenant-groups", apiType: "TenantGroup", title: "Tenant groups", subtitle: "Groupings of tenant scope", addNoun: "tenant group" },
  { slug: "contacts", apiType: "Contact", title: "Contacts", subtitle: "People and contact records", addNoun: "contact" },
  { slug: "teams", apiType: "Team", title: "Teams", subtitle: "Operational or ownership teams", addNoun: "team" },
  { slug: "tags", apiType: "Tag", title: "Tags", subtitle: "Labels for objects (assign via API or future UI)", addNoun: "tag" },
  { slug: "statuses", apiType: "StatusDefinition", title: "Custom statuses", subtitle: "Per–resource-type status labels", addNoun: "custom status" },
  { slug: "rack-groups", apiType: "RackGroup", title: "Rack groups", subtitle: "Logical groupings of racks", addNoun: "rack group" },
  { slug: "rack-reservations", apiType: "RackReservation", title: "Rack reservations", subtitle: "Scheduled rack use", addNoun: "rack reservation" },
  { slug: "elevations", apiType: "RackElevation", title: "Elevations", subtitle: "Rack elevation drawings / images", addNoun: "elevation" },
  { slug: "virtual-chassis", apiType: "VirtualChassis", title: "Virtual chassis", subtitle: "Multi-node chassis groupings", addNoun: "virtual chassis" },
  { slug: "virtual-chassis-members", apiType: "VirtualChassisMember", title: "Virtual chassis members", subtitle: "Devices in a virtual chassis", addNoun: "virtual chassis member" },
  { slug: "virtual-device-contexts", apiType: "VirtualDeviceContext", title: "Virtual device contexts", subtitle: "VDC / logical device contexts", addNoun: "virtual device context" },
  { slug: "device-redundancy-groups", apiType: "DeviceRedundancyGroup", title: "Device redundancy groups", subtitle: "Device HA / clustering", addNoun: "device redundancy group" },
  {
    slug: "device-redundancy-group-members",
    apiType: "DeviceRedundancyGroupMember",
    title: "Device redundancy members",
    subtitle: "Devices in HA groups",
    addNoun: "device redundancy member",
  },
  {
    slug: "interface-redundancy-groups",
    apiType: "InterfaceRedundancyGroup",
    title: "Interface redundancy groups",
    subtitle: "LAG / redundancy by interface",
    addNoun: "interface redundancy group",
  },
  {
    slug: "interface-redundancy-group-members",
    apiType: "InterfaceRedundancyGroupMember",
    title: "Interface redundancy members",
    subtitle: "Interfaces in LAG / redundancy groups",
    addNoun: "interface redundancy member",
  },
  { slug: "interfaces", apiType: "Interface", title: "Interfaces", subtitle: "Network interfaces on devices", addNoun: "interface" },
  { slug: "front-ports", apiType: "FrontPort", title: "Front ports", subtitle: "Patch-panel front ports", addNoun: "front port" },
  { slug: "rear-ports", apiType: "RearPort", title: "Rear ports", subtitle: "Patch-panel rear ports", addNoun: "rear port" },
  { slug: "console-ports", apiType: "ConsolePort", title: "Console ports", subtitle: "Device console (DTE) ports", addNoun: "console port" },
  { slug: "console-server-ports", apiType: "ConsoleServerPort", title: "Console server ports", subtitle: "Console server aggregation ports", addNoun: "console server port" },
  { slug: "power-ports", apiType: "PowerPort", title: "Power ports", subtitle: "Device power inputs", addNoun: "power port" },
  { slug: "power-outlets", apiType: "PowerOutlet", title: "Power outlets", subtitle: "PDU outlets", addNoun: "power outlet" },
  { slug: "device-bays", apiType: "DeviceBay", title: "Device bays", subtitle: "Child device slots", addNoun: "device bay" },
  { slug: "module-bays", apiType: "ModuleBay", title: "Module bays", subtitle: "Pluggable module slots", addNoun: "module bay" },
  { slug: "inventory-items", apiType: "InventoryItem", title: "Inventory items", subtitle: "Tracked hardware / parts", addNoun: "inventory item" },
  { slug: "modules", apiType: "Module", title: "Modules", subtitle: "Installed pluggable modules", addNoun: "module" },
  { slug: "module-types", apiType: "ModuleType", title: "Module types", subtitle: "Module hardware definitions (global)", addNoun: "module type" },
  { slug: "platforms", apiType: "SoftwarePlatform", title: "Platforms", subtitle: "Network OS / software platforms (global)", addNoun: "platform" },
  { slug: "software-versions", apiType: "SoftwareVersion", title: "Software versions", subtitle: "Releases per platform (global)", addNoun: "software version" },
  { slug: "software-image-files", apiType: "SoftwareImageFile", title: "Software image files", subtitle: "Image binaries and checksums", addNoun: "software image file" },
  { slug: "cables", apiType: "Cable", title: "Cables", subtitle: "Interface-to-interface links", addNoun: "cable" },
  { slug: "console-connections", apiType: "ConsoleConnection", title: "Console connections", subtitle: "Console path wiring", addNoun: "console connection" },
  { slug: "power-connections", apiType: "PowerConnection", title: "Power connections", subtitle: "Outlet-to-device power mapping", addNoun: "power connection" },
  { slug: "controllers", apiType: "Controller", title: "Controllers", subtitle: "BMC / automation controllers", addNoun: "controller" },
  { slug: "device-groups", apiType: "DeviceGroup", title: "Device groups", subtitle: "Static membership groups of devices", addNoun: "device group" },
  { slug: "namespaces", apiType: "IpamNamespace", title: "Namespaces", subtitle: "IPAM namespace scope (org)", addNoun: "namespace" },
  { slug: "route-targets", apiType: "RouteTarget", title: "Route targets", subtitle: "BGP / MPLS route targets", addNoun: "route target" },
  { slug: "rirs", apiType: "Rir", title: "RIRs", subtitle: "Regional Internet Registries (global)", addNoun: "RIR" },
  { slug: "vlan-groups", apiType: "VlanGroup", title: "VLAN groups", subtitle: "Logical groupings for VLANs (global)", addNoun: "VLAN group" },
  { slug: "circuit-types", apiType: "CircuitType", title: "Circuit types", subtitle: "Transport / service classifications (global)", addNoun: "circuit type" },
  {
    slug: "circuit-diversity-groups",
    apiType: "CircuitDiversityGroup",
    title: "Circuit diversity groups",
    subtitle: "Logical diversity sets for parallel / backup paths",
    addNoun: "circuit diversity group",
  },
  { slug: "provider-networks", apiType: "ProviderNetwork", title: "Provider networks", subtitle: "Carrier / provider network identifiers", addNoun: "provider network" },
  { slug: "circuit-terminations", apiType: "CircuitTermination", title: "Circuit terminations", subtitle: "A/Z hand-off points", addNoun: "circuit termination" },
  { slug: "circuit-segments", apiType: "CircuitSegment", title: "Circuit segments", subtitle: "Ordered legs of WAN / transport circuits", addNoun: "circuit segment" },
  { slug: "power-panels", apiType: "PowerPanel", title: "Power panels", subtitle: "Electrical panels by location", addNoun: "power panel" },
  { slug: "power-feeds", apiType: "PowerFeed", title: "Power feeds", subtitle: "Circuits and feeds", addNoun: "power feed" },
  { slug: "cloud-networks", apiType: "CloudNetwork", title: "Cloud networks", subtitle: "VPC / cloud network objects", addNoun: "cloud network" },
  { slug: "cloud-services", apiType: "CloudService", title: "Cloud services", subtitle: "Managed services in cloud networks", addNoun: "cloud service" },
  { slug: "wireless-networks", apiType: "WirelessNetwork", title: "Wireless networks", subtitle: "Wi‑Fi / SSID inventory", addNoun: "wireless network" },
  { slug: "vpns", apiType: "Vpn", title: "VPNs", subtitle: "VPN contexts", addNoun: "VPN" },
  { slug: "clusters", apiType: "Cluster", title: "Clusters", subtitle: "Compute / K8s-style clusters", addNoun: "cluster" },
  { slug: "virtual-machines", apiType: "VirtualMachine", title: "Virtual machines", subtitle: "VMs and guests", addNoun: "virtual machine" },
  { slug: "mpls", apiType: "MplsDomain", title: "MPLS domains", subtitle: "MPLS / L3VPN domains", addNoun: "MPLS domain" },
  { slug: "service-instances", apiType: "ServiceInstance", title: "Service instances", subtitle: "Logical service inventory (AS1-style)", addNoun: "service instance" },
];

export function catalogBySlug(slug: string): CatalogPageDef | undefined {
  return INVENTORY_CATALOG.find((c) => c.slug === slug);
}

/** URL slug for `/inventory/:slug/...` from API resource type (e.g. `Manufacturer` → `manufacturers`). */
export function catalogSlugForApiType(apiType: string): string | undefined {
  return INVENTORY_CATALOG.find((c) => c.apiType === apiType)?.slug;
}
