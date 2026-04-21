import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function FormPageShell({
  title,
  subtitle,
  backTo,
  backLabel = "Back to list",
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  backTo: string;
  backLabel?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <>
      <header className="main-header form-page-header">
        <div className="page-title-block">
          <Link to={backTo} className="form-back-link">
            ← {backLabel}
          </Link>
          <h2 className="page-title">{title}</h2>
          {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
        </div>
      </header>
      <div className="main-body form-page-body">
        {children}
        {footer ? <div className="form-page-footer">{footer}</div> : null}
      </div>
    </>
  );
}
