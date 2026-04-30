import { useQuery } from "@tanstack/react-query";
import { apiJson } from "../api/client";
import { useOptionalPageContext } from "./PageContext";
import { evalMacroBindings } from "./macros";
import { getWidgetComponent } from "./widgetRegistry";

type Placement = {
  id: string;
  pageId: string;
  slot: string;
  widgetKey: string;
  priority: number;
  macroBindings: Record<string, string>;
  filters?: unknown;
  requiredPermissions?: unknown;
  pluginPackageName?: string | null;
};

export function Slot({ name, pageId, resourceType }: { name: string; pageId: string; resourceType?: string }) {
  const pageCtx = useOptionalPageContext();
  const q = useQuery({
    queryKey: ["ui-placements", pageId, resourceType ?? ""],
    queryFn: async () => {
      const p = new URLSearchParams({ pageId });
      if (resourceType) p.set("resourceType", resourceType);
      return apiJson<{ items: Placement[] }>(`/v1/ui/placements?${p.toString()}`);
    },
  });

  if (!pageCtx || q.isError) return null;

  const list = (q.data?.items ?? [])
    .filter((row) => row.slot === name)
    .filter((row) => Boolean(getWidgetComponent(row.widgetKey)));
  if (!list.length) return null;

  return (
    <div className="ext-slot" data-slot={name} data-page-id={pageId}>
      {list.map((row) => {
        const Cmp = getWidgetComponent(row.widgetKey);
        if (!Cmp) return null;
        const props = evalMacroBindings(
          { ...row.macroBindings } as Record<string, unknown>,
          pageCtx,
        );
        return <Cmp key={row.id} {...props} />;
      })}
    </div>
  );
}

export function useSlotHasPlacements(
  pageId: string,
  slot: string,
  resourceType: string | undefined,
): { has: boolean; loading: boolean } {
  const q = useQuery({
    queryKey: ["ui-placements", pageId, resourceType ?? ""],
    queryFn: async () => {
      const p = new URLSearchParams({ pageId });
      if (resourceType) p.set("resourceType", resourceType);
      return apiJson<{ items: Placement[] }>(`/v1/ui/placements?${p.toString()}`);
    },
  });
  const has =
    (q.data?.items ?? []).some(
      (row) => row.slot === slot && getWidgetComponent(row.widgetKey) !== null,
    ) && !q.isError;
  return { has, loading: q.isLoading || q.isFetching };
}
