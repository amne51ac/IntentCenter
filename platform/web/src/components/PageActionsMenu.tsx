import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useId, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { apiJson } from "../api/client";
import { downloadBulkExport } from "../lib/bulkDownload";
import { importBulkCsv, importBulkJson } from "../lib/bulkImport";

type PinnedPage = { path: string; label: string };

type Me = {
  preferences?: { pinnedPages?: PinnedPage[] };
  auth: { mode: "user" } | { mode: "api_token" };
};

/**
 * Header ⋯ menu: Pin page, bulk import (CSV / JSON file pickers), bulk export (CSV / JSON).
 */
export function PageActionsMenu({
  pageLabel,
  resourceType,
  showPin = true,
  showBulk = true,
  onBulkSuccess,
}: {
  pageLabel: string;
  /** API resource type for `/v1/bulk/{type}/…` */
  resourceType?: string | null;
  showPin?: boolean;
  showBulk?: boolean;
  onBulkSuccess?: () => void;
}) {
  const location = useLocation();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const csvInputRef = useRef<HTMLInputElement>(null);
  const jsonInputRef = useRef<HTMLInputElement>(null);
  const menuId = useId();

  const me = useQuery({
    queryKey: ["me"],
    queryFn: () => apiJson<Me>("/v1/me"),
  });

  const patchPrefs = useMutation({
    mutationFn: (preferences: Record<string, unknown>) =>
      apiJson("/v1/me", { method: "PATCH", body: JSON.stringify({ preferences }) }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["me"] }),
  });

  const isUser = me.data?.auth?.mode === "user";
  const pinned = (me.data?.preferences?.pinnedPages ?? []) as PinnedPage[];
  const path = location.pathname;
  const isPinned = pinned.some((p) => p.path === path);

  function togglePin() {
    let next: PinnedPage[];
    if (isPinned) {
      next = pinned.filter((p) => p.path !== path);
    } else {
      next = [...pinned, { path, label: pageLabel }];
    }
    patchPrefs.mutate({ pinnedPages: next });
    setOpen(false);
  }

  useEffect(() => {
    if (!open) return;
    function handle(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
        setExportOpen(false);
      }
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setOpen(false);
        setExportOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  async function runExport(format: "csv" | "json") {
    if (!resourceType) return;
    try {
      await downloadBulkExport(resourceType, format, false);
    } catch (e) {
      window.alert(String(e));
    }
    setOpen(false);
    setExportOpen(false);
  }

  async function onCsvFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f || !resourceType) return;
    try {
      const r = await importBulkCsv(resourceType, f, false);
      window.alert(`Imported ${r.created} row(s).`);
      onBulkSuccess?.();
    } catch (err) {
      window.alert(String(err));
    }
    setOpen(false);
  }

  async function onJsonFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f || !resourceType) return;
    try {
      const r = await importBulkJson(resourceType, f, false);
      window.alert(`Imported ${r.created} row(s).`);
      onBulkSuccess?.();
    } catch (err) {
      window.alert(String(err));
    }
    setOpen(false);
  }

  const showMenu = (showPin && isUser) || (showBulk && resourceType);

  if (!showMenu) {
    return null;
  }

  return (
    <div className="page-actions-wrap" ref={rootRef}>
      <input ref={csvInputRef} type="file" accept=".csv,text/csv" className="sr-only" aria-hidden onChange={onCsvFile} />
      <input ref={jsonInputRef} type="file" accept=".json,application/json" className="sr-only" aria-hidden onChange={onJsonFile} />
      <button
        type="button"
        className="btn btn-ghost btn-page-actions-trigger"
        aria-expanded={open}
        aria-haspopup="menu"
        aria-controls={open ? menuId : undefined}
        onClick={() => setOpen((o) => !o)}
      >
        ⋯
      </button>
      {open ? (
        <ul id={menuId} className="page-actions-menu" role="menu">
          {showPin && isUser ? (
            <li role="none">
              <button type="button" role="menuitem" className="page-actions-item" onClick={() => togglePin()} disabled={patchPrefs.isPending}>
                {isPinned ? "Unpin page" : "Pin page"}
              </button>
            </li>
          ) : null}
          {showBulk && resourceType ? (
            <>
              {resourceType !== "Tenant" ? (
                <>
                  <li role="none">
                    <button
                      type="button"
                      role="menuitem"
                      className="page-actions-item"
                      onClick={() => {
                        csvInputRef.current?.click();
                      }}
                    >
                      Import CSV…
                    </button>
                  </li>
                  <li role="none">
                    <button
                      type="button"
                      role="menuitem"
                      className="page-actions-item"
                      onClick={() => {
                        jsonInputRef.current?.click();
                      }}
                    >
                      Import JSON…
                    </button>
                  </li>
                </>
              ) : null}
              <li className="page-actions-submenu-li" role="none">
                <button
                  type="button"
                  className="page-actions-item page-actions-item-expand"
                  aria-expanded={exportOpen}
                  onClick={() => setExportOpen((x) => !x)}
                >
                  Export <span aria-hidden>▸</span>
                </button>
                {exportOpen ? (
                  <ul className="page-actions-submenu" role="menu">
                    <li role="none">
                      <button type="button" role="menuitem" className="page-actions-item" onClick={() => void runExport("csv")}>
                        Export CSV
                      </button>
                    </li>
                    <li role="none">
                      <button type="button" role="menuitem" className="page-actions-item" onClick={() => void runExport("json")}>
                        Export JSON
                      </button>
                    </li>
                  </ul>
                ) : null}
              </li>
            </>
          ) : null}
        </ul>
      ) : null}
    </div>
  );
}
