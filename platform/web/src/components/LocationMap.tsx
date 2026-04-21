import { useEffect, useMemo } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "../leafletSetup";
import "leaflet/dist/leaflet.css";

export type LocationMapPoint = {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
};

function FitBounds({ positions }: { positions: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (positions.length === 0) return;
    if (positions.length === 1) {
      const p = positions[0]!;
      map.setView(p, 13);
      return;
    }
    const b = L.latLngBounds(positions);
    map.fitBounds(b, { padding: [28, 28], maxZoom: 12 });
  }, [map, positions]);
  return null;
}

export function rowToMapPoint(row: {
  id: string;
  name: string;
  latitude?: number | null;
  longitude?: number | null;
}): LocationMapPoint | null {
  const { latitude: lat, longitude: lng } = row;
  if (lat == null || lng == null) return null;
  if (typeof lat !== "number" || typeof lng !== "number") return null;
  if (Number.isNaN(lat) || Number.isNaN(lng)) return null;
  return { id: row.id, name: row.name, latitude: lat, longitude: lng };
}

type LocationMapProps = {
  points: LocationMapPoint[];
  /** CSS height of the map container (e.g. 280 or "min(50vh, 420px)") */
  height?: number | string;
  /** Emphasize one marker (opens popup is left to user / first render) */
  highlightId?: string;
  className?: string;
  emptyMessage?: string;
};

export function LocationMap({
  points,
  height = 320,
  highlightId,
  className,
  emptyMessage = "No coordinates yet. Edit a location and set latitude and longitude.",
}: LocationMapProps) {
  const positions = useMemo(() => points.map((p) => [p.latitude, p.longitude] as [number, number]), [points]);
  const center = useMemo((): [number, number] => {
    if (points.length === 1) return [points[0]!.latitude, points[0]!.longitude];
    return [39.8283, -98.5795];
  }, [points]);

  if (points.length === 0) {
    return <p className="muted">{emptyMessage}</p>;
  }

  const defaultZoom = points.length === 1 ? 13 : 4;

  return (
    <div
      className={className ? `location-map-wrap ${className}` : "location-map-wrap"}
      style={{ height, width: "100%", borderRadius: "var(--radius-md, 8px)", overflow: "hidden" }}
    >
      <MapContainer
        center={center}
        zoom={defaultZoom}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom
      >
        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {points.map((p) => (
          <Marker
            key={p.id}
            position={[p.latitude, p.longitude]}
            opacity={highlightId && p.id !== highlightId ? 0.65 : 1}
          >
            <Popup>
              <span className="location-map-popup-name">{p.name}</span>
            </Popup>
          </Marker>
        ))}
        <FitBounds positions={positions} />
      </MapContainer>
    </div>
  );
}
