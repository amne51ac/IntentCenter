import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { PageActionsMenu } from "./PageActionsMenu";

export type ModelListPageHeaderProps = {
  title: string;
  subtitle?: ReactNode;
  pinLabel?: string;
  addNew?: { to: string; label: string };
  /**
   * API resource type for `/v1/bulk/{type}/…` (import/export). Omit when bulk is not applicable.
   */
  bulkResourceType?: string | null;
  extraActions?: ReactNode;
  showPin?: boolean;
  showBulkTools?: boolean;
  onBulkSuccess?: () => void;
};

export function ModelListPageHeader({
  title,
  subtitle,
  pinLabel,
  addNew,
  bulkResourceType,
  extraActions,
  showPin = true,
  showBulkTools = true,
  onBulkSuccess,
}: ModelListPageHeaderProps) {
  const pin = pinLabel ?? title;
  const hasRightToolbar = showPin || addNew || showBulkTools || Boolean(extraActions);

  return (
    <header className="main-header">
      <div className="page-title-block">
        <h2 className="page-title">{title}</h2>
        {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
      </div>
      {hasRightToolbar ? (
        <div className="main-header-actions">
          {extraActions}
          <PageActionsMenu
            pageLabel={pin}
            resourceType={showBulkTools ? bulkResourceType ?? null : null}
            showPin={showPin}
            showBulk={Boolean(showBulkTools && bulkResourceType)}
            onBulkSuccess={onBulkSuccess}
          />
          {addNew ? (
            <Link to={addNew.to} className="btn btn-primary">
              {addNew.label}
            </Link>
          ) : null}
        </div>
      ) : null}
    </header>
  );
}
