import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { apiJson } from "../api/client";
import { useOptionalPageContext } from "./PageContext";
import { evalMacroBindings } from "./macros";
import { getWidgetComponent } from "./widgetRegistry";

type Placement = {
  id: string;
  pageId: string;
  slot: string;
  widgetKey: string;
  macroBindings: Record<string, string>;
};

type MeLite = { organization: { id: string; name: string; slug: string } };

/**
 * When `?debugWidgets=1` (or `localStorage.nimsDebugWidgets=1`), shows page context, placements, and
 * macro-evaluated props (support / traceability).
 */
export function ExtensionDebug({
  pageId,
  resourceType,
}: {
  pageId: string;
  resourceType: string;
}) {
  const [sp] = useSearchParams();
  const urlOn = sp.get("debugWidgets") === "1";
  const storageOn = typeof localStorage !== "undefined" && localStorage.getItem("nimsDebugWidgets") === "1";
  const pageCtx = useOptionalPageContext();

  const me = useQuery({
    queryKey: ["me"],
    queryFn: () => apiJson<MeLite>("/v1/me"),
  });

  const pl = useQuery({
    queryKey: ["ui-placements", pageId, resourceType],
    queryFn: async () => {
      const p = new URLSearchParams({ pageId });
      if (resourceType) p.set("resourceType", resourceType);
      return apiJson<{ items: Placement[] }>(`/v1/ui/placements?${p.toString()}`);
    },
  });

  if (!urlOn && !storageOn) {
    return null;
  }
  if (!pageCtx) {
    return null;
  }

  const items = (pl.data?.items ?? []) as Placement[];
  const perWidget = items.map((row) => {
    const Cmp = getWidgetComponent(row.widgetKey);
    const props = evalMacroBindings(
      { ...(row.macroBindings as Record<string, unknown>) },
      pageCtx,
    );
    return { row, hasComponent: Cmp != null, props };
  });

  return (
    <div className="ext-debug" role="region" aria-label="Extension debug">
      <h4 className="ext-debug-title">Extension debug</h4>
      <p className="ext-debug-hint muted">
        Shown when <code>?debugWidgets=1</code> or <code>localStorage.nimsDebugWidgets=1</code>. Remove before
        screenshots in production.
      </p>
      <div className="ext-debug-block">
        <h5>Organization (session)</h5>
        <pre className="ext-debug-pre mono">{JSON.stringify(me.data?.organization, null, 2)}</pre>
      </div>
      <div className="ext-debug-block">
        <h5>Page context (macros)</h5>
        <pre className="ext-debug-pre mono">{JSON.stringify(pageCtx, null, 2)}</pre>
      </div>
      <div className="ext-debug-block">
        <h5>Placements (API)</h5>
        <pre className="ext-debug-pre mono">{JSON.stringify(items, null, 2)}</pre>
      </div>
      <div className="ext-debug-block">
        <h5>Evaluated macro props per placement</h5>
        <pre className="ext-debug-pre mono">{JSON.stringify(perWidget, null, 2)}</pre>
      </div>
    </div>
  );
}
