import { useEffect, useState, type ReactNode } from "react";

const storageKey = (id: string) => `nims.sidebar.${id}`;

export function CollapsibleNavSection({
  id,
  title,
  defaultOpen = true,
  children,
}: {
  id: string;
  title: string;
  defaultOpen?: boolean;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);

  useEffect(() => {
    try {
      const v = localStorage.getItem(storageKey(id));
      if (v === "0") setOpen(false);
      if (v === "1") setOpen(true);
    } catch {
      /* ignore */
    }
  }, [id]);

  function toggle() {
    setOpen((o) => {
      const next = !o;
      try {
        localStorage.setItem(storageKey(id), next ? "1" : "0");
      } catch {
        /* ignore */
      }
      return next;
    });
  }

  return (
    <div className="nav-section nav-section-collapsible">
      <button type="button" className="nav-section-toggle" onClick={toggle} aria-expanded={open}>
        <span className="nav-section-toggle-label">{title}</span>
        <span className="nav-section-chevron" aria-hidden>
          {open ? "▼" : "▶"}
        </span>
      </button>
      {open ? <div className="nav-section-children">{children}</div> : null}
    </div>
  );
}
