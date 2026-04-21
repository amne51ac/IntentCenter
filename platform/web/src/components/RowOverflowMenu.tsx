import { createPortal } from "react-dom";
import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from "react";

export type OverflowMenuItem = {
  id: string;
  label: string;
  onSelect: () => void;
  /** Visually emphasized as destructive */
  danger?: boolean;
};

/**
 * Kebab / three-dots menu for table rows. Stops propagation so row click does not fire.
 */
export function RowOverflowMenu({ items, ariaLabel = "Row actions" }: { items: OverflowMenuItem[]; ariaLabel?: string }) {
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLUListElement>(null);
  const [menuPos, setMenuPos] = useState<{ top: number; right: number } | null>(null);
  const listId = useId();

  const updateMenuPosition = useCallback(() => {
    const el = buttonRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    setMenuPos({ top: rect.bottom + 4, right: window.innerWidth - rect.right });
  }, []);

  useLayoutEffect(() => {
    if (!open) {
      setMenuPos(null);
      return;
    }
    updateMenuPosition();
    window.addEventListener("resize", updateMenuPosition);
    document.addEventListener("scroll", updateMenuPosition, true);
    return () => {
      window.removeEventListener("resize", updateMenuPosition);
      document.removeEventListener("scroll", updateMenuPosition, true);
    };
  }, [open, updateMenuPosition]);

  useEffect(() => {
    if (!open) return;
    function handle(e: MouseEvent) {
      const t = e.target as Node;
      if (buttonRef.current?.contains(t)) return;
      if (menuRef.current?.contains(t)) return;
      setOpen(false);
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  const menu =
    open && menuPos ? (
      <ul
        ref={menuRef}
        id={listId}
        className="row-overflow-menu row-overflow-menu-portal"
        role="menu"
        style={{ top: menuPos.top, right: menuPos.right }}
      >
        {items.map((it) => (
          <li key={it.id} role="none">
            <button
              type="button"
              role="menuitem"
              className={"row-overflow-item" + (it.danger ? " row-overflow-item-danger" : "")}
              onClick={() => {
                setOpen(false);
                it.onSelect();
              }}
            >
              {it.label}
            </button>
          </li>
        ))}
      </ul>
    ) : null;

  return (
    <div className={"row-overflow" + (open ? " row-overflow-open" : "")} onClick={(e) => e.stopPropagation()}>
      <button
        ref={buttonRef}
        type="button"
        className="btn-overflow"
        aria-label={ariaLabel}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-controls={open ? listId : undefined}
        onClick={() => setOpen((o) => !o)}
      >
        ⋯
      </button>
      {menu ? createPortal(menu, document.body) : null}
    </div>
  );
}
