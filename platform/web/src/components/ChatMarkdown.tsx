import type { ReactNode } from "react";
import type { Components } from "react-markdown";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
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
  center: [number, number];
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

function parseMapSpec(raw: string): MapSpec | null {
  const t = raw.trim();
  if (!t) return null;
  try {
    const o = JSON.parse(t) as MapSpec;
    if (!o || !Array.isArray(o.center) || o.center.length !== 2) return null;
    const [a, b] = o.center;
    if (typeof a !== "number" || typeof b !== "number" || !Number.isFinite(a) || !Number.isFinite(b)) return null;
    if (Math.abs(a) > 90 || Math.abs(b) > 180) return null;
    return o;
  } catch {
    return null;
  }
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

function MapFromSpec({ spec }: { spec: MapSpec }) {
  const zoom = Math.min(18, Math.max(1, spec.zoom ?? 3));
  const [lat, lon] = spec.center;
  const marks = (spec.markers || []).filter(
    (m) => typeof m.lat === "number" && typeof m.lng === "number" && Number.isFinite(m.lat) && Number.isFinite(m.lng)
  );
  return (
    <div className="ai-assistant-map-wrap">
      {spec.title ? <div className="ai-assistant-map-title">{spec.title}</div> : null}
      <div className="ai-assistant-map-canvas" style={{ width: "100%" }}>
        <MapContainer
          center={[lat, lon] as [number, number]}
          zoom={zoom}
          style={{ width: "100%", height: 200, borderRadius: 8, zIndex: 0 }}
          scrollWheelZoom={false}
        >
          <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {marks.map((m, i) => (
            <CircleMarker key={i} center={[m.lat, m.lng] as [number, number]} radius={6} pathOptions={{ color: "var(--accent)", fillColor: "var(--accent)", fillOpacity: 0.55 }}>
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
            return (
              <li key={i}>
                {action ? <span className="ai-assistant-proposal-action">{action}</span> : null}{" "}
                {rtype || rid ? (
                  <span className="ai-assistant-proposal-target">
                    {rtype}
                    {rid ? ` · ${rid.slice(0, 8)}…` : ""}
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
        return <div className="ai-assistant-chart-err">Could not render map. Expect JSON with center [lat,lon] and optional markers.</div>;
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
  return (
    <div className={variant === "user" ? "ai-assistant-md ai-assistant-md--user" : "ai-assistant-md"}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
        {text}
      </ReactMarkdown>
    </div>
  );
}
