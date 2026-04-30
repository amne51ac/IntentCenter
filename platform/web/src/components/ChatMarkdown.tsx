import type { ReactNode } from "react";
import { useEffect, useMemo, useRef } from "react";
import type { Components } from "react-markdown";
import { Link } from "react-router-dom";
import L from "leaflet";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import ReactMarkdown from "react-markdown";
import "leaflet/dist/leaflet.css";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import remarkGfm from "remark-gfm";
import { linkifyInventoryReferences } from "../lib/linkifyObjectRefs";

export type ChatMarkdownVariant = "assistant" | "user";

type ChartSpec = {
  v?: number;
  kind?: string;
  type?: string;
  title?: string;
  xKey?: string;
  yKey?: string;
  nameKey?: string;
  valueKey?: string;
  data: Array<Record<string, unknown>>;
};

type MapSpec = {
  v?: number;
  /** Optional when `markers` has at least one point; UI will frame markers. */
  center?: [number, number];
  zoom?: number;
  title?: string;
  markers?: Array<{ lat: number; lng: number; label?: string }>;
};

type ProposalSpec = {
  v?: number;
  summary?: string;
  changes?: Array<Record<string, unknown>>;
  readOnly?: boolean;
  disclaimer?: string;
};

function parseChartSpec(raw: string): ChartSpec | null {
  const t = raw.trim();
  if (!t) return null;
  try {
    const o = JSON.parse(t) as ChartSpec;
    if (!o || !Array.isArray(o.data) || o.data.length === 0) return null;
    const k = String(o.kind || o.type || "bar").toLowerCase();
    if (k === "pie") {
      if (typeof o.nameKey !== "string" || typeof o.valueKey !== "string") return null;
    } else {
      if (typeof o.xKey !== "string" || typeof o.yKey !== "string") return null;
    }
    return o;
  } catch {
    return null;
  }
}

/** Coerce JSON / LLM output numbers (including numeric strings) to a finite number or null. */
function parseCoordComponent(v: unknown): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const t = v.trim().replace(/,/g, "");
    if (!t) return null;
    const n = Number.parseFloat(t);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function isValidLatLon(a: number, b: number): boolean {
  return Math.abs(a) <= 90 && Math.abs(b) <= 180;
}

/**
 * One map marker from flexible shapes: { lat, lng } | { latitude, longitude } | { coordinates: [a,b] } | string coords.
 */
function parseMapMarkerObject(m: unknown): { lat: number; lng: number; label?: string } | null {
  if (!m || typeof m !== "object" || Array.isArray(m)) return null;
  const rec = m as Record<string, unknown>;
  let lat = parseCoordComponent(rec.lat ?? rec.latitude);
  let lng = parseCoordComponent(rec.lng ?? rec.longitude ?? rec.lon ?? rec.long);
  if (lat == null || lng == null) {
    const c = rec.coordinates ?? rec.coord ?? rec.position;
    if (Array.isArray(c) && c.length >= 2) {
      lat = parseCoordComponent(c[0]);
      lng = parseCoordComponent(c[1]);
    } else if (c && typeof c === "object" && !Array.isArray(c)) {
      const p = c as Record<string, unknown>;
      lat = parseCoordComponent(p.lat ?? p.latitude);
      lng = parseCoordComponent(p.lng ?? p.longitude ?? p.lon);
    }
  }
  if (lat == null || lng == null || !isValidLatLon(lat, lng)) return null;
  const label =
    rec.label != null
      ? String(rec.label)
      : rec.name != null
        ? String(rec.name)
        : rec.title != null
          ? String(rec.title)
          : undefined;
  return { lat, lng, label };
}

/** Parse map JSON; tolerate ``` fences, leading prose, and alternate top-level array keys. */
function parseMapJsonObject(raw: string): Record<string, unknown> | null {
  const t0 = raw.trim();
  if (!t0) return null;
  const tryParse = (s: string): Record<string, unknown> | null => {
    try {
      const v = JSON.parse(s) as unknown;
      if (v && typeof v === "object" && !Array.isArray(v)) return v as Record<string, unknown>;
      if (Array.isArray(v) && v.length > 0) return { markers: v };
      return null;
    } catch {
      return null;
    }
  };
  let o = tryParse(t0);
  if (o) return o;
  const fence = t0.match(/```(?:json|map)?\s*([\s\S]*?)```/i);
  if (fence?.[1]) o = tryParse(fence[1].trim());
  if (o) return o;
  const start = t0.indexOf("{");
  const end = t0.lastIndexOf("}");
  if (start >= 0 && end > start) {
    o = tryParse(t0.slice(start, end + 1).trim());
    if (o) return o;
  }
  return null;
}

function parseMapCenter(o: Record<string, unknown>): [number, number] | undefined {
  const c = o.center;
  if (Array.isArray(c) && c.length === 2) {
    const a = parseCoordComponent(c[0]);
    const b = parseCoordComponent(c[1]);
    if (a != null && b != null && isValidLatLon(a, b)) return [a, b];
  }
  if (c && typeof c === "object" && !Array.isArray(c)) {
    const r = c as Record<string, unknown>;
    const a = parseCoordComponent(r.lat ?? r.latitude);
    const b = parseCoordComponent(r.lng ?? r.longitude ?? r.lon ?? r.long);
    if (a != null && b != null && isValidLatLon(a, b)) return [a, b];
  }
  return undefined;
}

function parseMapSpec(raw: string): MapSpec | null {
  const t = raw.trim();
  if (!t) return null;
  const o = parseMapJsonObject(t);
  if (!o) return null;
  const rawList =
    o.markers ??
    o.points ??
    o.places ??
    o.locations ??
    (Array.isArray(o["data"]) ? o["data"] : undefined);
  const rawMarks = Array.isArray(rawList) ? rawList : [];
  const markers: Array<{ lat: number; lng: number; label?: string }> = [];
  for (const m of rawMarks) {
    const pm = parseMapMarkerObject(m);
    if (pm) markers.push(pm);
  }
  let center: [number, number] | undefined = parseMapCenter(o);
  if (!center && markers.length > 0) {
    const sum = markers.reduce(
      (acc, m) => [acc[0] + m.lat, acc[1] + m.lng] as [number, number],
      [0, 0] as [number, number],
    );
    center = [sum[0] / markers.length, sum[1] / markers.length];
  }
  if (!center) return null;
  const title = o.title != null ? String(o.title) : undefined;
  const zoom = typeof o.zoom === "number" && Number.isFinite(o.zoom) ? o.zoom : undefined;
  return {
    v: typeof o.v === "number" ? o.v : undefined,
    center,
    zoom,
    title,
    markers: markers.length > 0 ? markers : undefined,
  };
}

function parseProposalSpec(raw: string): ProposalSpec | null {
  const t = raw.trim();
  if (!t) return null;
  try {
    const o = JSON.parse(t) as ProposalSpec;
    if (!o) return null;
    return o;
  } catch {
    return null;
  }
}

function kindOf(spec: ChartSpec): string {
  return String(spec.kind || spec.type || "bar").toLowerCase();
}

const PIE_COLORS = ["var(--accent)", "rgba(232,184,78,0.85)", "#5ba3d0", "#8b7cb8", "#5aa387"];

function ChartFromSpec({ spec }: { spec: ChartSpec }) {
  const { data, xKey, yKey, nameKey, valueKey, title } = spec;
  const k = kindOf(spec);
  if (k === "pie" && nameKey && valueKey) {
    const rows = data.map((row) => {
      const yv = row[valueKey];
      const n = typeof yv === "number" ? yv : Number(yv);
      return { ...row, [valueKey]: Number.isFinite(n) ? n : 0, name: String(row[nameKey] ?? "") } as Record<
        string,
        unknown
      >;
    });
    return (
      <div className="ai-assistant-chart-wrap">
        {title ? <div className="ai-assistant-chart-title">{title}</div> : null}
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Tooltip
              contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: 6 }}
            />
            <Pie
              data={rows as Array<Record<string, string | number>>}
              dataKey={valueKey}
              nameKey={nameKey}
              innerRadius={36}
              outerRadius={72}
              paddingAngle={2}
            >
              {rows.map((_, i) => (
                <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} stroke="var(--bg-app)" />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }
  if (!xKey || !yKey) return <div className="ai-assistant-chart-err">Invalid chart: missing xKey or yKey.</div>;
  const rows = data.map((row) => {
    const yv = row[yKey];
    const n = typeof yv === "number" ? yv : Number(yv);
    return { ...row, [yKey]: Number.isFinite(n) ? n : 0 } as Record<string, unknown>;
  });
  if (k === "area") {
    return (
      <div className="ai-assistant-chart-wrap">
        {title ? <div className="ai-assistant-chart-title">{title}</div> : null}
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={rows} margin={{ top: 6, right: 8, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis dataKey={xKey} tick={{ fontSize: 11 }} stroke="var(--text-low)" />
            <YAxis tick={{ fontSize: 11 }} stroke="var(--text-low)" width={40} />
            <Tooltip
              contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: 6 }}
            />
            <Area type="monotone" dataKey={yKey} stroke="var(--accent)" fill="var(--accent)" fillOpacity={0.25} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    );
  }
  if (k === "line") {
    return (
      <div className="ai-assistant-chart-wrap">
        {title ? <div className="ai-assistant-chart-title">{title}</div> : null}
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={rows} margin={{ top: 6, right: 8, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis dataKey={xKey} tick={{ fontSize: 11 }} stroke="var(--text-low)" />
            <YAxis tick={{ fontSize: 11 }} stroke="var(--text-low)" width={40} />
            <Tooltip
              contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: 6 }}
            />
            <Line type="monotone" dataKey={yKey} stroke="var(--accent)" strokeWidth={2} dot={{ r: 2 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }
  return (
    <div className="ai-assistant-chart-wrap">
      {title ? <div className="ai-assistant-chart-title">{title}</div> : null}
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={rows} margin={{ top: 6, right: 8, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
          <XAxis dataKey={xKey} tick={{ fontSize: 11 }} stroke="var(--text-low)" />
          <YAxis tick={{ fontSize: 11 }} stroke="var(--text-low)" width={40} />
          <Tooltip
            contentStyle={{ background: "var(--bg-elevated)", border: "1px solid var(--border)", borderRadius: 6 }}
          />
          <Bar dataKey={yKey} fill="var(--accent)" radius={[4, 4, 0, 0]} maxBarSize={48} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** After mount, zoom/pan to show all markers (fixes continent-scale default when the model picks zoom 3). */
function MapFitBounds({ points, boundsKey }: { points: [number, number][]; boundsKey: string }) {
  const map = useMap();
  const pointsRef = useRef(points);
  pointsRef.current = points;

  useEffect(() => {
    const pts = pointsRef.current;
    if (pts.length === 0) return;
    const id = requestAnimationFrame(() => {
      const p = pointsRef.current;
      if (p.length === 0) return;
      if (p.length === 1) {
        map.setView(p[0], 12, { animate: false });
        map.invalidateSize();
        return;
      }
      const latLngs = p.map((q) => L.latLng(q[0], q[1]));
      const b = L.latLngBounds(latLngs);
      if (!b.isValid()) {
        map.setView(p[0], 12, { animate: false });
        map.invalidateSize();
        return;
      }
      const ne = b.getNorthEast();
      const sw = b.getSouthWest();
      const samePoint = ne.lat === sw.lat && ne.lng === sw.lng;
      if (samePoint) {
        map.setView(p[0], 14, { animate: false });
      } else {
        map.fitBounds(b, { padding: [32, 32], maxZoom: 16, animate: false });
      }
      map.invalidateSize();
    });
    return () => cancelAnimationFrame(id);
  }, [map, boundsKey]);

  return null;
}


function MapFromSpec({ spec }: { spec: MapSpec }) {
  const marks = useMemo(() => {
    return (spec.markers || []).filter(
      (m) => typeof m.lat === "number" && typeof m.lng === "number" && Number.isFinite(m.lat) && Number.isFinite(m.lng)
    );
  }, [spec.markers]);
  const positions: [number, number][] = useMemo(() => marks.map((m) => [m.lat, m.lng] as [number, number]), [marks]);
  const boundsKey = useMemo(
    () =>
      [...positions]
        .map((p) => `${p[0].toFixed(5)},${p[1].toFixed(5)}`)
        .sort()
        .join("|"),
    [positions]
  );

  const zoom = Math.min(18, Math.max(1, spec.zoom ?? 3));
  const center = spec.center;
  if (!center) {
    return <div className="ai-assistant-chart-err">Map is missing a valid center or markers.</div>;
  }
  const [lat, lon] = center;

  return (
    <div className="ai-assistant-map-wrap">
      {spec.title ? <div className="ai-assistant-map-title">{spec.title}</div> : null}
      <div className="ai-assistant-map-canvas" style={{ width: "100%" }}>
        <MapContainer
          center={[lat, lon] as [number, number]}
          zoom={zoom}
          style={{ width: "100%", height: 240, borderRadius: 8, zIndex: 0 }}
          scrollWheelZoom={false}
        >
          <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {positions.length > 0 ? <MapFitBounds points={positions} boundsKey={boundsKey} /> : null}
          {marks.map((m, i) => (
            <CircleMarker
              key={i}
              center={[m.lat, m.lng] as [number, number]}
              radius={9}
              pathOptions={{
                color: "#0d0d0f",
                weight: 2,
                fillColor: "var(--accent)",
                fillOpacity: 0.9,
              }}
            >
              {m.label ? <Popup>{m.label}</Popup> : null}
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}

function ProposalFromSpec({ spec }: { spec: ProposalSpec }) {
  return (
    <div className="ai-assistant-proposal-wrap">
      <div className="ai-assistant-proposal-badge">Preview only</div>
      {spec.summary ? <div className="ai-assistant-proposal-summary">{spec.summary}</div> : null}
      {Array.isArray(spec.changes) && spec.changes.length > 0 ? (
        <ul className="ai-assistant-proposal-list">
          {spec.changes.map((c, i) => {
            if (!c || typeof c !== "object") return <li key={i}>(invalid entry)</li>;
            const o = c as Record<string, unknown>;
            const action = o.action != null ? String(o.action) : "";
            const rtype = o.resource_type != null ? String(o.resource_type) : "";
            const rid = o.resource_id != null ? String(o.resource_id) : "";
            const why = o.rationale != null ? String(o.rationale) : "";
            const linkTo =
              rtype && rid && rid.length > 20 ? `/o/${encodeURIComponent(rtype)}/${encodeURIComponent(rid)}` : null;
            return (
              <li key={i}>
                {action ? <span className="ai-assistant-proposal-action">{action}</span> : null}{" "}
                {rtype || rid ? (
                  <span className="ai-assistant-proposal-target">
                    {rtype}
                    {rid && linkTo ? (
                      <>
                        {" "}
                        <Link to={linkTo} className="ai-md-link">
                          {rid.slice(0, 8)}…
                        </Link>
                      </>
                    ) : rid ? (
                      ` · ${rid.slice(0, 8)}…`
                    ) : null}
                  </span>
                ) : null}
                {why ? <div className="ai-assistant-proposal-rationale">{why}</div> : null}
              </li>
            );
          })}
        </ul>
      ) : null}
      {spec.disclaimer ? <div className="ai-assistant-proposal-foot">{spec.disclaimer}</div> : null}
    </div>
  );
}

function makeComponents(): Partial<Components> {
  return {
    a: (props) => {
      const { href, children, className, ...rest } = props;
      if (typeof href === "string" && href.startsWith("/") && !href.startsWith("//")) {
        return (
          <Link
            to={href}
            className={className ? `ai-md-link ${className}` : "ai-md-link"}
            {...(rest as Record<string, unknown>)}
          >
            {children}
          </Link>
        );
      }
      return (
        <a
          href={typeof href === "string" ? href : undefined}
          className={className ? `ai-md-link ${className}` : "ai-md-link"}
          target="_blank"
          rel="noopener noreferrer"
          {...(rest as Record<string, unknown>)}
        >
          {children}
        </a>
      );
    },
    pre: ({ children }: { children?: ReactNode }) => (
      <div className="ai-assistant-fence-wrap">{children}</div>
    ),
    code: (props) => {
      const { className, children, ...rest } = props;
      const raw = String(children).replace(/\n$/, "");
      if (className?.includes("language-chart")) {
        const sp = parseChartSpec(raw);
        if (sp) return <ChartFromSpec spec={sp} />;
        return (
          <div className="ai-assistant-chart-err">
            Could not render chart. For bar/line/area use xKey, yKey, and data. For pie use nameKey, valueKey, and
            data.
          </div>
        );
      }
      if (className?.includes("language-map")) {
        const sp = parseMapSpec(raw);
        if (sp) return <MapFromSpec spec={sp} />;
        return (
          <div className="ai-assistant-chart-err">
            Could not render map. Use JSON with a markers array (lat, lng) and optional title; center is optional
            if markers are present (the view zooms to fit all markers).
          </div>
        );
      }
      if (className?.includes("language-proposal")) {
        const sp = parseProposalSpec(raw);
        if (sp) return <ProposalFromSpec spec={sp} />;
        return <div className="ai-assistant-chart-err">Could not parse change proposal JSON.</div>;
      }
      if (!className) {
        return (
          <code className="ai-assistant-md-inline" {...rest}>
            {children}
          </code>
        );
      }
      return (
        <code className={className + " ai-assistant-md-blockcode"} {...rest}>
          {children}
        </code>
      );
    },
  };
}

const mdComponents = makeComponents();

export function ChatMarkdown({ text, variant = "assistant" }: { text: string; variant?: ChatMarkdownVariant }) {
  const forMd = useMemo(
    () => (variant === "assistant" ? linkifyInventoryReferences(text) : text),
    [text, variant],
  );
  return (
    <div className={variant === "user" ? "ai-assistant-md ai-assistant-md--user" : "ai-assistant-md"}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
        {forMd}
      </ReactMarkdown>
    </div>
  );
}
