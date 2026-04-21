import { Link, useParams } from "react-router-dom";

function titleFromSlug(slug: string): string {
  return slug
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

const NOTES: Record<string, string> = {
  "ip-address-assignments":
    "IntentCenter stores address-to-interface attachment on each IP address row today; a dedicated assignment table may be added later.",
  statuses: "Device and circuit status values are enums on core models, not a separate status catalog yet.",
  "interface-connections": "Physical interface-to-interface links are modeled as cables between interfaces.",
};

export function ComingSoonPage() {
  const { slug = "" } = useParams<{ slug: string }>();
  const title = titleFromSlug(slug || "feature");
  const note = NOTES[slug];

  return (
    <>
      <header className="main-header">
        <div className="page-title-block">
          <h2 className="page-title">{title}</h2>
          <p className="page-subtitle">
            Not in the current IntentCenter schema — planned to align with NetBox-style DCIM / IPAM objects.
          </p>
        </div>
      </header>
      <div className="main-body">
        <p>
          This object type does not have a database table or API surface yet. If you need it prioritized, extend the Prisma schema and regenerate
          models, or track it as a product requirement.
        </p>
        {note ? <p className="muted">{note}</p> : null}
        <p>
          <Link to="/" className="form-back-link">
            ← Back to overview
          </Link>
        </p>
      </div>
    </>
  );
}
