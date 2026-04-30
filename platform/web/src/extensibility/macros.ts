import type { PageContextValue } from "./PageContext";

const ALLOWED_ROOTS = new Set(["page", "resource", "user", "organization"]);

function getByPath(obj: unknown, path: string): unknown {
  const parts = path.split(".").filter(Boolean);
  if (parts.length === 0) return undefined;
  if (!ALLOWED_ROOTS.has(parts[0]!)) return undefined;
  let cur: unknown = obj;
  for (const p of parts) {
    if (cur === null || cur === undefined) return undefined;
    if (typeof cur !== "object") return undefined;
    cur = (cur as Record<string, unknown>)[p];
  }
  return cur;
}

function macroObjectFromContext(ctx: PageContextValue): Record<string, unknown> {
  return {
    page: {
      ...ctx.page,
    },
    resource: ctx.resource,
    user: ctx.user,
    organization: ctx.organization,
  };
}

/**
 * v1: `{{ dot.path }}` only, roots: page, resource, user, organization.
 * Renders to empty string for missing values.
 */
export function evalMacroTemplate(template: string, ctx: PageContextValue): string {
  const root = macroObjectFromContext(ctx);
  return template.replace(/\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}/g, (_match, path: string) => {
    const v = getByPath(root, String(path).trim());
    if (v === null || v === undefined) return "";
    if (typeof v === "object" && v !== null && !Array.isArray(v)) {
      return JSON.stringify(v);
    }
    return String(v);
  });
}

export function evalMacroBindings(
  raw: Record<string, unknown> | null | undefined,
  ctx: PageContextValue,
): Record<string, string> {
  const out: Record<string, string> = {};
  if (!raw || typeof raw !== "object") return out;
  for (const [k, v] of Object.entries(raw)) {
    if (typeof v === "string") {
      out[k] = evalMacroTemplate(v, ctx);
    }
  }
  return out;
}
