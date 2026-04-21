import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useId, useMemo } from "react";
import { apiJson } from "../../api/client";
import { InlineLoader } from "../../components/Loader";
import { objectEditHref, objectViewHref, resourceTypeForApi } from "../../lib/objectLinks";
import { LocationMap, rowToMapPoint } from "../../components/LocationMap";

type Node = { resourceType: string; id: string; label: string; meta?: Record<string, unknown> };
type Edge = {
  kind: string;
  label: string;
  from: { resourceType: string; id: string };
  to: { resourceType: string; id: string };
};
type TreeN = { node: Node; children: TreeN[] };

type HardwarePortRow = { id: string; name: string; label?: string | null; type?: string | null };

type HardwareSlotPayload = {
  bay: { id: string; name: string | null; position?: number | null };
  card: HardwareCardPayload | null;
};

type HardwareCardPayload = {
  id: string;
  serial?: string | null;
  moduleTypeId?: string;
  moduleType?: { id: string; model: string; partNumber?: string | null };
  slots: HardwareSlotPayload[];
  frontPorts: HardwarePortRow[];
};

type DeviceHardwarePayload = {
  deviceId: string;
  deviceName: string;
  chassisFrontPorts: HardwarePortRow[];
  slots: HardwareSlotPayload[];
};

type ResourceViewPayload = {
  item: Record<string, unknown>;
  graph: { root: Node; nodes: Node[]; edges: Edge[]; tree: TreeN } | null;
  hardware?: DeviceHardwarePayload | null;
};

function nk(t: string, id: string): string {
  return `${t}:${id}`;
}

/** Stable hue from type name for subtle node tinting. */
function typeHue(resourceType: string): number {
  let h = 0;
  for (let i = 0; i < resourceType.length; i++) {
    h = (h * 33 + resourceType.charCodeAt(i)) % 360;
  }
  return h;
}

/** Where a ray from (cx,cy) toward (tx,ty) exits the axis-aligned rect centered at (cx,cy). */
function rectRayExit(
  cx: number,
  cy: number,
  hw: number,
  hh: number,
  tx: number,
  ty: number,
): { x: number; y: number } {
  const dx = tx - cx;
  const dy = ty - cy;
  const len = Math.hypot(dx, dy);
  if (len < 1e-9) return { x: cx + hw, y: cy };
  const ux = dx / len;
  const uy = dy / len;
  const ts: number[] = [];
  const pushIf = (t: number, ok: boolean) => {
    if (t > 1e-9 && ok) ts.push(t);
  };
  if (ux > 1e-9) {
    const t = hw / ux;
    const y = cy + t * uy;
    pushIf(t, y >= cy - hh - 1e-5 && y <= cy + hh + 1e-5);
  }
  if (ux < -1e-9) {
    const t = (-hw) / ux;
    const y = cy + t * uy;
    pushIf(t, y >= cy - hh - 1e-5 && y <= cy + hh + 1e-5);
  }
  if (uy > 1e-9) {
    const t = hh / uy;
    const x = cx + t * ux;
    pushIf(t, x >= cx - hw - 1e-5 && x <= cx + hw + 1e-5);
  }
  if (uy < -1e-9) {
    const t = (-hh) / uy;
    const x = cx + t * ux;
    pushIf(t, x >= cx - hw - 1e-5 && x <= cx + hw + 1e-5);
  }
  const tEdge = ts.length ? Math.min(...ts) : Math.min(hw / (Math.abs(ux) + 1e-9), hh / (Math.abs(uy) + 1e-9));
  return { x: cx + tEdge * ux, y: cy + tEdge * uy };
}

function edgeBetweenRects(
  ax: number,
  ay: number,
  hwa: number,
  hha: number,
  bx: number,
  by: number,
  hwb: number,
  hhb: number,
): { x1: number; y1: number; x2: number; y2: number } {
  const p1 = rectRayExit(ax, ay, hwa, hha, bx, by);
  const p2 = rectRayExit(bx, by, hwb, hhb, ax, ay);
  return { x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y };
}

const NODE_W_ROOT = 136;
const NODE_H_ROOT = 66;
const NODE_W_SAT = 128;
const NODE_H_SAT = 62;
const NODE_RX = 10;

/** Minimum gap between node boxes on the relationship map (SVG px). */
const REL_MAP_GAP = 28;
/** Padding inside the SVG viewBox. */
const REL_MAP_PAD = 40;
/** Ellipse vertical radius = ring × this factor (horizontal uses full `ring`). */
const REL_MAP_Y_FACTOR = 0.88;
/** Radial gap before the next concentric ring (prevents ring-on-ring overlap). */
const REL_RING_RADIAL_STEP = NODE_H_SAT + REL_MAP_GAP + 18;

function edgeCaption(e: Edge): string {
  const human = (e.label || "").trim();
  if (human) return human;
  return (e.kind || "relationship").replace(/_/g, " ");
}

function RelationshipDiagram({
  root,
  nodes,
  edges,
}: {
  root: Node;
  nodes: Node[];
  edges: Edge[];
}) {
  const navigate = useNavigate();
  const markerUid = useId().replace(/:/g, "");
  const arrowMarkerId = `rel-arrow-${markerUid}`;

  const layout = useMemo(() => {
    const rk = nk(root.resourceType, root.id);
    const others = nodes.filter((n) => nk(n.resourceType, n.id) !== rk);

    /* Minimum radius so the root box and the innermost satellite ring do not overlap. */
    const minRingSep = Math.max(
      NODE_W_ROOT / 2 + NODE_W_SAT / 2 + REL_MAP_GAP,
      (NODE_H_ROOT / 2 + NODE_H_SAT / 2 + REL_MAP_GAP) / REL_MAP_Y_FACTOR,
    );

    /* On a ring of radius R, adjacent satellite centers must be at least chordMin apart (ellipse-safe). */
    const chordMin = NODE_W_SAT + REL_MAP_GAP;
    const yS = Math.min(1, REL_MAP_Y_FACTOR);

    function minRadiusForSatelliteCount(k: number): number {
      if (k <= 1) return minRingSep;
      return Math.max(minRingSep, chordMin / (2 * yS * Math.sin(Math.PI / k)));
    }

    /** Largest k ≤ maxWant such that k nodes fit on a ring of radius R without overlap. */
    function maxSatellitesThatFitRing(R: number, maxWant: number): number {
      let lo = 1;
      let hi = Math.max(maxWant, 1);
      let best = 0;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        if (mid <= 1 || minRadiusForSatelliteCount(mid) <= R + 1e-6) {
          best = mid;
          lo = mid + 1;
        } else {
          hi = mid - 1;
        }
      }
      return best;
    }

    const raw = new Map<string, { x: number; y: number }>();
    raw.set(rk, { x: 0, y: 0 });

    let ringR = minRingSep;
    let idx = 0;
    while (idx < others.length) {
      const rem = others.length - idx;
      let k = maxSatellitesThatFitRing(ringR, rem);
      if (k === 0) {
        ringR += 14;
        continue;
      }
      for (let j = 0; j < k; j++) {
        const n = others[idx + j]!;
        const angle = (2 * Math.PI * j) / k - Math.PI / 2;
        raw.set(nk(n.resourceType, n.id), {
          x: Math.cos(angle) * ringR,
          y: Math.sin(angle) * (ringR * REL_MAP_Y_FACTOR),
        });
      }
      idx += k;
      if (idx >= others.length) break;
      ringR += REL_RING_RADIAL_STEP;
    }

    let minX = Infinity;
    let maxX = -Infinity;
    let minY = Infinity;
    let maxY = -Infinity;
    for (const n of nodes) {
      const p = raw.get(nk(n.resourceType, n.id));
      if (!p) continue;
      const isRoot = nk(n.resourceType, n.id) === rk;
      const hw = isRoot ? NODE_W_ROOT / 2 : NODE_W_SAT / 2;
      const hh = isRoot ? NODE_H_ROOT / 2 : NODE_H_SAT / 2;
      minX = Math.min(minX, p.x - hw);
      maxX = Math.max(maxX, p.x + hw);
      minY = Math.min(minY, p.y - hh);
      maxY = Math.max(maxY, p.y + hh);
    }
    if (!Number.isFinite(minX)) {
      minX = -80;
      maxX = 80;
      minY = -80;
      maxY = 80;
    }

    const ox = REL_MAP_PAD - minX;
    const oy = REL_MAP_PAD - minY;
    const w = Math.ceil(Math.max(400, maxX - minX + 2 * REL_MAP_PAD));
    const h = Math.ceil(Math.max(320, maxY - minY + 2 * REL_MAP_PAD));

    const pos = new Map<string, { x: number; y: number }>();
    for (const [key, p] of raw.entries()) {
      pos.set(key, { x: p.x + ox, y: p.y + oy });
    }

    const rootP = pos.get(rk)!;
    return { w, h, cx: rootP.x, cy: rootP.y, pos, rootKey: rk };
  }, [root, nodes]);

  const nodeHalf = useMemo(() => {
    const m = new Map<string, { hw: number; hh: number }>();
    for (const n of nodes) {
      const k = nk(n.resourceType, n.id);
      if (k === layout.rootKey) {
        m.set(k, { hw: NODE_W_ROOT / 2, hh: NODE_H_ROOT / 2 });
      } else {
        m.set(k, { hw: NODE_W_SAT / 2, hh: NODE_H_SAT / 2 });
      }
    }
    return m;
  }, [nodes, layout.rootKey]);

  const edgeGraphics = useMemo(() => {
    const { pos } = layout;
    const showEdgeLabels = edges.length <= 72;
    const strokeAlpha = edges.length > 120 ? 0.22 : edges.length > 72 ? 0.34 : 0.55;
    return edges
      .map((e, i) => {
        const a = pos.get(nk(e.from.resourceType, e.from.id));
        const b = pos.get(nk(e.to.resourceType, e.to.id));
        if (!a || !b) return null;
        const ha = nodeHalf.get(nk(e.from.resourceType, e.from.id)) ?? {
          hw: NODE_W_SAT / 2,
          hh: NODE_H_SAT / 2,
        };
        const hb = nodeHalf.get(nk(e.to.resourceType, e.to.id)) ?? {
          hw: NODE_W_SAT / 2,
          hh: NODE_H_SAT / 2,
        };
        const { x1, y1, x2, y2 } = edgeBetweenRects(a.x, a.y, ha.hw, ha.hh, b.x, b.y, hb.hw, hb.hh);
        const mx = (x1 + x2) / 2;
        const my = (y1 + y2) / 2;
        const dx = x2 - x1;
        const dy = y2 - y1;
        const len = Math.hypot(dx, dy) || 1;
        const px = -dy / len;
        const py = dx / len;
        const cap = edgeCaption(e);
        const short =
          cap.length > 36 ? `${cap.slice(0, 34)}…` : cap;
        const lx = mx + px * 18;
        const ly = my + py * 18;
        return (
          <g key={`e-${i}-${e.from.id}-${e.to.id}-${e.kind}`} className="object-view-edge">
            <title>
              {e.label} ({e.kind}) — {e.from.resourceType} → {e.to.resourceType}
            </title>
            <line
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={`rgba(139, 151, 171, ${strokeAlpha})`}
              strokeWidth={1.35}
              markerEnd={`url(#${arrowMarkerId})`}
            />
            {showEdgeLabels ? (
              <text
                x={lx}
                y={ly}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="var(--text-muted)"
                fontSize={9}
                fontFamily="var(--font-sans)"
                fontWeight={500}
                className="object-view-edge-label"
              >
                {short}
              </text>
            ) : null}
          </g>
        );
      })
      .filter(Boolean);
  }, [edges, layout, nodeHalf, arrowMarkerId]);

  return (
    <div className="object-view-viz-wrap">
      <svg
        className="object-view-viz-svg"
        viewBox={`0 0 ${layout.w} ${layout.h}`}
        width="100%"
        height={layout.h}
        role="img"
        aria-label="Relationship diagram: objects as boxes, arrows show relationship direction"
      >
        <defs>
          <marker
            id={arrowMarkerId}
            markerWidth="7"
            markerHeight="7"
            refX="6"
            refY="3.5"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L7,3.5 L0,7 z" fill="rgba(139, 151, 171, 0.75)" />
          </marker>
        </defs>
        <rect width="100%" height="100%" fill="transparent" />
        {edgeGraphics}
        {nodes.map((n) => {
          const p = layout.pos.get(nk(n.resourceType, n.id));
          if (!p) return null;
          const isRoot = nk(n.resourceType, n.id) === layout.rootKey;
          const bw = isRoot ? NODE_W_ROOT : NODE_W_SAT;
          const bh = isRoot ? NODE_H_ROOT : NODE_H_SAT;
          const hue = typeHue(n.resourceType);
          const fillSat = isRoot ? "rgba(201, 162, 39, 0.2)" : `hsla(${hue}, 26%, 38%, 0.32)`;
          const strokeSat = isRoot ? "var(--accent)" : `hsla(${hue}, 38%, 52%, 0.9)`;
          const displayName = (n.label || n.id).trim();
          const nameLine = displayName.length > 26 ? `${displayName.slice(0, 24)}…` : displayName;
          const typeLine =
            n.resourceType.length > 22 ? `${n.resourceType.slice(0, 20)}…` : n.resourceType;
          const idShort = n.id.length > 14 ? `${n.id.slice(0, 10)}…` : n.id;
          return (
            <g
              key={nk(n.resourceType, n.id)}
              style={{ cursor: "pointer" }}
              onClick={() => navigate(objectViewHref(n.resourceType, n.id))}
              className="object-view-graph-node"
            >
              <rect
                x={p.x - bw / 2}
                y={p.y - bh / 2}
                width={bw}
                height={bh}
                rx={NODE_RX}
                ry={NODE_RX}
                fill={fillSat}
                stroke={strokeSat}
                strokeWidth={isRoot ? 2 : 1.5}
              />
              <title>
                {n.resourceType}
                {"\n"}
                {displayName}
                {"\n"}
                ID: {n.id}
              </title>
              <text
                x={p.x}
                y={p.y - 13}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="var(--text-muted)"
                fontSize={8.5}
                fontWeight={600}
                fontFamily="var(--font-sans)"
                letterSpacing="0.03em"
                className="object-view-node-type"
              >
                {typeLine}
              </text>
              <text
                x={p.x}
                y={p.y + 4}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="var(--text)"
                fontSize={10.5}
                fontFamily="var(--font-sans)"
                fontWeight={650}
                className="object-view-node-name"
              >
                {nameLine}
              </text>
              <text
                x={p.x}
                y={p.y + 20}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="var(--text-muted)"
                fontSize={7.75}
                fontFamily="var(--font-mono)"
                opacity={0.9}
                className="object-view-node-id"
              >
                {idShort}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="object-view-graph-summary" aria-live="polite">
        <span className="object-view-graph-summary-stat">
          <strong>{nodes.length}</strong> objects
        </span>
        <span className="object-view-graph-summary-sep">·</span>
        <span className="object-view-graph-summary-stat">
          <strong>{edges.length}</strong> directed relationships
        </span>
        <span className="object-view-graph-summary-hint">
          {nodes.length > 14
            ? "Many neighbors are arranged on concentric rings. Scroll the diagram when it is larger than the frame. "
            : ""}
          Arrows point from → to. Labels match the relationships table.
        </span>
      </div>
      <p className="muted object-view-viz-hint">
        Click a box to open that object.
        {edges.length > 72
          ? " With very many links, edge captions are hidden to reduce clutter; use the relationships table or hover a line for details."
          : " Edge labels describe the link; tooltips include type, name, and full id."}
      </p>
    </div>
  );
}

function TreeBranch({ tree }: { tree: TreeN }) {
  return (
    <li>
      <Link to={objectViewHref(tree.node.resourceType, tree.node.id)}>
        <span className="badge">{tree.node.resourceType}</span> {tree.node.label}
      </Link>
      {tree.children?.length ? (
        <ul className="rel-tree-nested">
          {tree.children.map((c, i) => (
            <TreeBranch key={i} tree={c} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

function TreeView({ tree }: { tree: TreeN }) {
  return (
    <ul className="rel-tree">
      <TreeBranch tree={tree} />
    </ul>
  );
}

type TopoProvider = { id?: string; name?: string };
type TopoSeg = {
  id: string;
  segmentIndex: number;
  label?: string | null;
  bandwidthMbps?: number | null;
  status?: string;
  provider?: TopoProvider | null;
};
type TopoTerm = {
  id: string;
  side?: string;
  portName?: string | null;
  description?: string | null;
  location?: { id?: string; name?: string } | null;
};

function CircuitTerminationCard({ side, term }: { side: string; term: TopoTerm }) {
  const loc = term.location;
  return (
    <div className="circuit-path-node circuit-path-node--term">
      <span className="circuit-path-node-kicker">{side}-side</span>
      <div className="circuit-path-node-title">
        {loc?.id ? (
          <Link to={objectViewHref("Location", loc.id)}>{loc.name ?? "Location"}</Link>
        ) : (
          <span className="muted">No location</span>
        )}
      </div>
      {term.portName ? <div className="circuit-path-node-meta mono">{term.portName}</div> : null}
      {term.description ? <div className="circuit-path-node-hint">{term.description}</div> : null}
    </div>
  );
}

function CircuitSegmentCard({ seg }: { seg: TopoSeg }) {
  const pv = seg.provider;
  return (
    <div className="circuit-path-node circuit-path-node--segment">
      <span className="circuit-path-node-kicker">Leg {seg.segmentIndex}</span>
      <div className="circuit-path-node-title">{seg.label?.trim() || `Segment ${seg.segmentIndex}`}</div>
      <div className="circuit-path-node-meta">
        {pv?.id ? (
          <Link to={objectViewHref("Provider", pv.id)}>{pv.name ?? "Provider"}</Link>
        ) : (
          <span className="muted">—</span>
        )}
        {seg.bandwidthMbps != null ? ` · ${seg.bandwidthMbps} Mbps` : ""}
        {seg.status ? ` · ${seg.status}` : ""}
      </div>
      <Link className="circuit-path-seg-link" to={objectViewHref("CircuitSegment", seg.id)}>
        Segment record
      </Link>
    </div>
  );
}

function CircuitTopologySection({ item }: { item: Record<string, unknown> }) {
  const segs = (Array.isArray(item.segments) ? item.segments : []) as TopoSeg[];
  const terms = (Array.isArray(item.terminations) ? item.terminations : []) as TopoTerm[];
  const sortedSegs = [...segs].sort((a, b) => (a.segmentIndex ?? 0) - (b.segmentIndex ?? 0));
  const aT = terms.find((t) => String(t.side || "").toUpperCase() === "A");
  const zT = terms.find((t) => String(t.side || "").toUpperCase() === "Z");
  const divGroup = item.circuitDiversityGroup as { id?: string; name?: string; slug?: string } | null | undefined;

  const hasPath = sortedSegs.length > 0 || Boolean(aT) || Boolean(zT);
  if (!hasPath && !divGroup?.id) {
    return null;
  }

  return (
    <section className="graph-section">
      <h3 className="graph-section-title">Circuit path</h3>
      {divGroup?.id ? (
        <p className="circuit-diversity-banner">
          Diversity group:{" "}
          <Link to={objectViewHref("CircuitDiversityGroup", divGroup.id)}>{divGroup.name ?? divGroup.slug ?? "View group"}</Link>
        </p>
      ) : null}
      {hasPath ? (
        <p className="circuit-path-lead muted">Ordered legs from A-side to Z-side, including carrier hand-offs.</p>
      ) : null}
      {hasPath ? (
        <div className="circuit-path-wrap">
          <div className="circuit-path" role="img" aria-label="Circuit topology from A-side through segments to Z-side">
            {aT ? (
              <>
                <CircuitTerminationCard side="A" term={aT} />
                {sortedSegs.length > 0 || zT ? <span className="circuit-path-connector">→</span> : null}
              </>
            ) : null}
            {sortedSegs.map((seg, i) => (
              <span key={seg.id} className="circuit-path-step">
                <CircuitSegmentCard seg={seg} />
                {i < sortedSegs.length - 1 || zT ? <span className="circuit-path-connector">→</span> : null}
              </span>
            ))}
            {zT ? <CircuitTerminationCard side="Z" term={zT} /> : null}
          </div>
        </div>
      ) : (
        <p className="muted">No segments or A/Z terminations yet.</p>
      )}
    </section>
  );
}

function formatDetailValue(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

function HardwareSlots({ slots, nested }: { slots: HardwareSlotPayload[]; nested?: boolean }) {
  if (!slots.length) return null;
  return (
    <ul className={nested ? "hardware-tree hardware-tree--nested" : "hardware-tree"}>
      {slots.map((s) => (
        <li key={s.bay.id}>
          <div className="hardware-bay">
            <span className="hardware-bay-name">{s.bay.name?.trim() || "Slot"}</span>
            {s.card ? (
              <>
                <span className="hardware-card-label">
                  {s.card.moduleType?.model ?? "Module"}
                  {s.card.serial ? ` · ${s.card.serial}` : ""}
                </span>
                {s.card.frontPorts?.length ? (
                  <ul className="hardware-ports">
                    {s.card.frontPorts.map((p) => (
                      <li key={p.id}>
                        Front port: {p.name}
                        {p.type ? ` (${p.type})` : ""}
                      </li>
                    ))}
                  </ul>
                ) : null}
                <HardwareSlots slots={s.card.slots} nested />
              </>
            ) : (
              <span className="muted">Empty slot</span>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

function HardwareSection({ hw }: { hw: DeviceHardwarePayload }) {
  const hasTree = hw.slots.length > 0 || hw.chassisFrontPorts.length > 0;
  if (!hasTree) {
    return (
      <section className="graph-section">
        <h3 className="graph-section-title">Hardware (slots &amp; cards)</h3>
        <p className="muted">No module bays or chassis front ports on this device.</p>
      </section>
    );
  }
  return (
    <section className="graph-section">
      <h3 className="graph-section-title">Hardware (slots &amp; cards)</h3>
      <div className="hardware-panel">
        {hw.chassisFrontPorts.length ? (
          <div>
            <div className="hardware-bay-name">Chassis front ports</div>
            <ul className="hardware-chassis-ports">
              {hw.chassisFrontPorts.map((p) => (
                <li key={p.id}>
                  {p.name}
                  {p.type ? ` (${p.type})` : ""}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {hw.slots.length ? <HardwareSlots slots={hw.slots} /> : null}
      </div>
    </section>
  );
}

export function ObjectViewPage() {
  const { resourceType = "", resourceId = "" } = useParams<{ resourceType: string; resourceId: string }>();
  const rtApi = resourceTypeForApi(decodeURIComponent(resourceType));
  const id = decodeURIComponent(resourceId);

  const q = useQuery({
    queryKey: ["resource-view", rtApi, id],
    queryFn: () =>
      apiJson<ResourceViewPayload>(`/v1/resource-view/${encodeURIComponent(rtApi)}/${encodeURIComponent(id)}`),
    enabled: Boolean(resourceType && resourceId),
  });

  const title =
    (q.data?.item?.name as string | undefined) ||
    (q.data?.item?.label as string | undefined) ||
    (q.data?.item?.cid as string | undefined) ||
    (q.data?.graph?.root?.label as string | undefined) ||
    rtApi;

  /** Use API-aligned type so `/o/Service/…` and `/o/ServiceInstance/…` behave like other views; DCIM edit URLs still keyed on Device/Location/Rack. */
  const editTo = objectEditHref(rtApi, id);

  return (
    <div className="main-page">
      <header className="main-header">
        <div className="page-title-block">
          <p className="header-meta">
            <span className="badge">{rtApi}</span>
            <span className="mono header-meta-id">{id}</span>
          </p>
          <h2 className="page-title">{title}</h2>
          <p className="page-subtitle page-subtitle--flush">
            <Link to="/" className="form-back-link">
              ← Home
            </Link>
          </p>
        </div>
        <div className="main-header-actions">
          {editTo ? (
            <Link to={editTo} className="btn btn-primary">
              Edit
            </Link>
          ) : null}
        </div>
      </header>
      <div className="main-body">
        {q.isLoading ? <InlineLoader label="Loading object…" /> : null}
        {q.error ? <div className="error-banner">{String(q.error)}</div> : null}
        {q.data ? (
          <>
            <section className="graph-section">
              <h3 className="graph-section-title">Details</h3>
              <dl className="object-view-details">
                {Object.keys(q.data.item)
                  .filter(
                    (key) =>
                      (rtApi !== "Circuit" ||
                        (key !== "segments" && key !== "terminations" && key !== "circuitDiversityGroup")) &&
                      (rtApi !== "Location" || (key !== "latitude" && key !== "longitude")),
                  )
                  .sort()
                  .map((key) => (
                    <div key={key} className="object-view-detail-row">
                      <dt>{key}</dt>
                      <dd className="mono">{formatDetailValue(q.data.item[key])}</dd>
                    </div>
                  ))}
              </dl>
            </section>

            {rtApi === "Location" ? (
              <section className="graph-section">
                <h3 className="graph-section-title">Map</h3>
                {(() => {
                  const item = q.data.item;
                  const name = typeof item.name === "string" ? item.name : "Location";
                  const pt = rowToMapPoint({
                    id,
                    name,
                    latitude: item.latitude as number | null | undefined,
                    longitude: item.longitude as number | null | undefined,
                  });
                  return pt ? (
                    <LocationMap key={id} points={[pt]} height={320} highlightId={id} />
                  ) : (
                    <p className="muted">No coordinates for this location. Use Edit to set latitude and longitude.</p>
                  );
                })()}
              </section>
            ) : null}

            {rtApi === "Circuit" ? <CircuitTopologySection item={q.data.item} /> : null}

            {rtApi === "Device" && q.data.hardware ? <HardwareSection hw={q.data.hardware} /> : null}

            {q.data.graph ? (
              <>
                <section className="graph-section">
                  <h3 className="graph-section-title">Relationship map</h3>
                  <RelationshipDiagram root={q.data.graph.root} nodes={q.data.graph.nodes} edges={q.data.graph.edges} />
                </section>
                <section className="graph-section">
                  <h3 className="graph-section-title">Tree</h3>
                  <div className="graph-tree-wrap">
                    <TreeView tree={q.data.graph.tree} />
                  </div>
                </section>
                <section className="graph-section">
                  <h3 className="graph-section-title">Relationships</h3>
                  <div className="table-wrap">
                    <table className="data">
                      <thead>
                        <tr>
                          <th>Relationship</th>
                          <th>From</th>
                          <th>To</th>
                        </tr>
                      </thead>
                      <tbody>
                        {q.data.graph.edges.map((e, i) => (
                          <tr key={i}>
                            <td>{e.label}</td>
                            <td>
                              <Link to={objectViewHref(e.from.resourceType, e.from.id)}>
                                {e.from.resourceType}: {e.from.id.slice(0, 8)}…
                              </Link>
                            </td>
                            <td>
                              <Link to={objectViewHref(e.to.resourceType, e.to.id)}>
                                {e.to.resourceType}: {e.to.id.slice(0, 8)}…
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
                <section className="graph-section">
                  <h3 className="graph-section-title">Related objects</h3>
                  <div className="table-wrap">
                    <table className="data">
                      <thead>
                        <tr>
                          <th>Type</th>
                          <th>Label</th>
                          <th />
                        </tr>
                      </thead>
                      <tbody>
                        {q.data.graph.nodes.map((n) => (
                          <tr key={`${n.resourceType}-${n.id}`}>
                            <td>
                              <span className="badge">{n.resourceType}</span>
                            </td>
                            <td>{n.label}</td>
                            <td className="table-actions">
                              <Link to={objectViewHref(n.resourceType, n.id)} className="btn btn-ghost table-inline-link">
                                View
                              </Link>
                              {objectEditHref(n.resourceType, n.id) ? (
                                <Link to={objectEditHref(n.resourceType, n.id)!} className="btn btn-ghost table-inline-link">
                                  Edit
                                </Link>
                              ) : null}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              </>
            ) : (
              <section className="graph-section">
                <p className="muted">No relationship graph could be loaded (the object may be missing or not visible).</p>
              </section>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}
