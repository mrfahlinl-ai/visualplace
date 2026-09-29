"use client";

import dynamic from "next/dynamic";
import {
  AlertTriangle,
  Check,
  Globe,
  MapPin,
  Navigation,
  ShieldQuestion,
  X,
} from "lucide-react";
import type { AnalysisRead } from "@/lib/types";
import { BAND_META, confidencePercent, placeLine, toneClasses } from "@/lib/format";
import type { MapPoint } from "@/components/map-view";

const MapView = dynamic(() => import("@/components/map-view"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center bg-muted text-sm text-muted-foreground">
      Loading map…
    </div>
  ),
});

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-border bg-card p-5">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h2>
      {children}
    </section>
  );
}

export function ResultView({ analysis }: { analysis: AnalysisRead }) {
  const band = analysis.confidence_band ?? "unknown";
  const meta = BAND_META[band];
  const pct = confidencePercent(analysis.confidence);
  const loc = analysis.final_location;
  const isUnknown = band === "unknown" || !loc;

  const primary: MapPoint | null = loc
    ? { latitude: loc.latitude, longitude: loc.longitude, label: loc.name, primary: true }
    : null;
  const candidatePoints: MapPoint[] = analysis.candidates
    .filter((c) => c.latitude != null && c.longitude != null && c.id !== undefined)
    .filter((c) => !(loc && c.rank === 1))
    .map((c) => ({
      latitude: c.latitude as number,
      longitude: c.longitude as number,
      label: c.name,
      rank: c.rank,
    }));

  const topCandidate =
    [...analysis.candidates].sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99))[0] ?? null;
  const radiusM = topCandidate?.radius_m ?? null;
  const hasMap = primary != null || candidatePoints.length > 0;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm text-muted-foreground">
              {isUnknown ? "Result" : "Most likely location"}
            </p>
            <h1 className="mt-1 flex items-center gap-2 text-2xl font-semibold tracking-tight">
              {isUnknown ? (
                <ShieldQuestion className="h-6 w-6 text-muted-foreground" aria-hidden />
              ) : (
                <MapPin className="h-6 w-6 text-primary" aria-hidden />
              )}
              {isUnknown ? "Unable to pinpoint" : placeLine(loc?.city, loc?.country)}
            </h1>
            {!isUnknown && loc?.name ? (
              <p className="mt-1 text-muted-foreground">{loc.name}</p>
            ) : null}
          </div>
          <div
            className={`flex flex-col items-end gap-1 rounded-xl border px-4 py-2 ${toneClasses(
              meta.tone,
            )}`}
          >
            {pct != null ? <span className="text-2xl font-bold">{pct}%</span> : null}
            <span className="text-xs font-medium">{meta.label}</span>
          </div>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">{meta.blurb}</p>
      </div>

      {/* Map */}
      {hasMap ? (
        <div className="h-80 overflow-hidden rounded-2xl border border-border">
          <MapView primary={primary} candidates={candidatePoints} radiusM={radiusM} />
        </div>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-2">
        {/* Why */}
        <Section title="Why we think this">
          {analysis.explanation.length ? (
            <ul className="space-y-2">
              {analysis.explanation.map((reason, i) => {
                const isContra = reason.startsWith("However:");
                return (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    {isContra ? (
                      <X className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" aria-hidden />
                    ) : (
                      <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" aria-hidden />
                    )}
                    <span>{reason}</span>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No supporting evidence available.</p>
          )}
        </Section>

        {/* Location details */}
        {loc ? (
          <Section title="Location details">
            <dl className="space-y-2 text-sm">
              {loc.name ? (
                <Detail label="Place" value={loc.name} icon={<MapPin className="h-4 w-4" />} />
              ) : null}
              {loc.address ? <Detail label="Address" value={loc.address} /> : null}
              {placeLine(loc.city, loc.country) ? (
                <Detail
                  label="Region"
                  value={placeLine(loc.city, loc.country)}
                  icon={<Globe className="h-4 w-4" />}
                />
              ) : null}
              <Detail
                label="Coordinates"
                value={`${loc.latitude.toFixed(5)}, ${loc.longitude.toFixed(5)}`}
                icon={<Navigation className="h-4 w-4" />}
              />
              {loc.place_type ? <Detail label="Type" value={loc.place_type} /> : null}
            </dl>
            <a
              href={`https://www.openstreetmap.org/?mlat=${loc.latitude}&mlon=${loc.longitude}#map=13/${loc.latitude}/${loc.longitude}`}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline"
            >
              Open in map <Navigation className="h-3.5 w-3.5" aria-hidden />
            </a>
          </Section>
        ) : null}
      </div>

      {/* Alternatives */}
      {analysis.candidates.length > 1 ? (
        <Section title="Alternative candidates">
          <ul className="space-y-2">
            {[...analysis.candidates]
              .sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99))
              .slice(1)
              .map((c) => (
                <li
                  key={c.id}
                  className="flex items-center justify-between gap-3 rounded-lg border border-border px-3 py-2 text-sm"
                >
                  <span className="flex items-center gap-2">
                    <span className="text-muted-foreground">#{c.rank}</span>
                    <span className="font-medium">{c.name}</span>
                    {c.country ? (
                      <span className="text-muted-foreground">· {c.country}</span>
                    ) : null}
                  </span>
                  <span className="tabular-nums text-muted-foreground">
                    {Math.round(c.score * 100)}%
                  </span>
                </li>
              ))}
          </ul>
        </Section>
      ) : null}

      {/* Evidence detail */}
      {topCandidate && topCandidate.evidence.length ? (
        <Section title="Evidence">
          <ul className="space-y-2">
            {topCandidate.evidence.map((ev, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                {ev.kind === "contradiction" ? (
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" aria-hidden />
                ) : (
                  <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" aria-hidden />
                )}
                <span>
                  <span className="text-muted-foreground">
                    [{ev.category.replace(/_/g, " ")}]
                  </span>{" "}
                  {ev.description}
                </span>
              </li>
            ))}
          </ul>
        </Section>
      ) : null}
    </div>
  );
}

function Detail({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <dt className="flex items-center gap-1.5 text-muted-foreground">
        {icon}
        {label}
      </dt>
      <dd className="text-right font-medium">{value}</dd>
    </div>
  );
}
