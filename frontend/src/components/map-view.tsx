"use client";

import { useEffect } from "react";
import L from "leaflet";
import { Circle, MapContainer, Marker, TileLayer, Tooltip, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export interface MapPoint {
  latitude: number;
  longitude: number;
  label: string;
  rank?: number | null;
  primary?: boolean;
}

interface MapViewProps {
  primary: MapPoint | null;
  candidates: MapPoint[];
  /** Accuracy radius in metres; when set, the primary point is shown as an area. */
  radiusM?: number | null;
}

function pinIcon(primary: boolean): L.DivIcon {
  return L.divIcon({
    className: "vp-pin",
    html: `<span style="display:block;width:18px;height:18px;border-radius:9999px;
      background:${primary ? "#4f46e5" : "#64748b"};border:2px solid white;
      box-shadow:0 1px 4px rgba(0,0,0,.4)"></span>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

function FitBounds({ points }: { points: MapPoint[] }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 0) return;
    if (points.length === 1) {
      map.setView([points[0].latitude, points[0].longitude], 12);
      return;
    }
    const bounds = L.latLngBounds(points.map((p) => [p.latitude, p.longitude]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 13 });
  }, [map, points]);
  return null;
}

export default function MapView({ primary, candidates, radiusM }: MapViewProps) {
  const allPoints = [...(primary ? [primary] : []), ...candidates];
  const center: [number, number] = primary
    ? [primary.latitude, primary.longitude]
    : allPoints.length
      ? [allPoints[0].latitude, allPoints[0].longitude]
      : [20, 0];

  return (
    <MapContainer
      center={center}
      zoom={primary ? 11 : 2}
      scrollWheelZoom={false}
      style={{ height: "100%", width: "100%" }}
      className="z-0"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds points={allPoints} />

      {primary && radiusM ? (
        <Circle
          center={[primary.latitude, primary.longitude]}
          radius={radiusM}
          pathOptions={{ color: "#4f46e5", fillColor: "#4f46e5", fillOpacity: 0.1 }}
        />
      ) : null}

      {candidates.map((c, i) => (
        <Marker
          key={`c-${i}`}
          position={[c.latitude, c.longitude]}
          icon={pinIcon(false)}
        >
          <Tooltip>{`#${c.rank ?? i + 1} ${c.label}`}</Tooltip>
        </Marker>
      ))}

      {primary ? (
        <Marker position={[primary.latitude, primary.longitude]} icon={pinIcon(true)}>
          <Tooltip permanent direction="top" offset={[0, -10]}>
            {primary.label}
          </Tooltip>
        </Marker>
      ) : null}
    </MapContainer>
  );
}
