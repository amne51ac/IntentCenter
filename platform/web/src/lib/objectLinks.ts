import { catalogSlugForApiType } from "../pages/inventory/inventoryCatalogConfig";

const VIEW_PREFIX = "/o";

/** Detail / relationship view (default destination from lists and search). */
export function objectViewHref(resourceType: string, id: string): string {
  return `${VIEW_PREFIX}/${encodeURIComponent(resourceType)}/${encodeURIComponent(id)}`;
}

/** @deprecated Prefer `objectViewHref` — kept for existing imports; opens the view page, not edit. */
export function objectHref(resourceType: string, id: string): string {
  return objectViewHref(resourceType, id);
}

/**
 * Map URL / graph resource type strings to stable PascalCase names (and Service → ServiceInstance).
 * Used so edit links match even when the path segment casing differs.
 */
export function normalizeObjectResourceType(resourceType: string): string {
  const trimmed = resourceType.trim();
  if (!trimmed) return trimmed;
  const apiAligned = resourceTypeForApi(trimmed);
  const key = apiAligned.replace(/\s+/g, "").toLowerCase();
  const dcim: Record<string, string> = {
    device: "Device",
    location: "Location",
    rack: "Rack",
  };
  return dcim[key] ?? apiAligned;
}

/**
 * Edit form URL when a screen exists.
 * Prefer first-class CRUD routes (IPAM, DCIM, …); otherwise inventory catalog edit.
 */
export function objectEditHref(resourceType: string, id: string): string | null {
  const t = normalizeObjectResourceType(resourceType);

  switch (t) {
    case "Location":
      return `/dcim/locations/${id}/edit`;
    case "Rack":
      return `/dcim/racks/${id}/edit`;
    case "Device":
      return `/dcim/devices/${id}/edit`;
    case "Vrf":
      return `/ipam/vrfs/${id}/edit`;
    case "Prefix":
      return `/ipam/prefixes/${id}/edit`;
    case "IpAddress":
      return `/ipam/ip-addresses/${id}/edit`;
    case "Vlan":
      return `/ipam/vlans/${id}/edit`;
    case "Provider":
      return `/circuits/providers/${id}/edit`;
    case "Circuit":
      return `/circuits/circuits/${id}/edit`;
    case "ServiceInstance":
    case "Service":
      return `/platform/services/${id}/edit`;
    case "JobDefinition":
      return `/platform/jobs/${id}/edit`;
    case "ObjectTemplate":
      return `/platform/object-templates/${id}/edit`;
    default:
      break;
  }

  const slug = catalogSlugForApiType(t);
  if (slug && t !== "Tenant") {
    return `/inventory/${slug}/${id}/edit`;
  }

  return null;
}

/** Map URL segment to API `resource_type` (e.g. Service → ServiceInstance). */
export function resourceTypeForApi(resourceType: string): string {
  if (resourceType === "Service") return "ServiceInstance";
  return resourceType;
}
