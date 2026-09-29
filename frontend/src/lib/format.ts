import type { ConfidenceBand } from "@/lib/types";

/** User-facing label + tone for each confidence band (spec §1, §33). */
export const BAND_META: Record<
  ConfidenceBand,
  { label: string; tone: "strong" | "good" | "medium" | "low"; blurb: string }
> = {
  exact_gps: {
    label: "Exact — GPS metadata",
    tone: "strong",
    blurb: "The photo's embedded GPS coordinates place it precisely.",
  },
  strong: {
    label: "Strong match",
    tone: "strong",
    blurb: "Multiple strong, consistent clues point to this location.",
  },
  probable: {
    label: "Probable",
    tone: "good",
    blurb: "Good evidence supports this location.",
  },
  approximate: {
    label: "Approximate area",
    tone: "medium",
    blurb: "Evidence suggests this general area, not an exact spot.",
  },
  weak: {
    label: "Weak / speculative",
    tone: "low",
    blurb: "Only weak clues — treat this as a rough guess.",
  },
  unknown: {
    label: "Unable to determine",
    tone: "low",
    blurb: "There wasn't enough reliable evidence to locate this photo.",
  },
};

export function confidencePercent(confidence: number | null): number | null {
  if (confidence == null) return null;
  return Math.round(confidence * 100);
}

export function toneClasses(tone: "strong" | "good" | "medium" | "low"): string {
  switch (tone) {
    case "strong":
      return "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30";
    case "good":
      return "bg-sky-500/15 text-sky-600 dark:text-sky-400 border-sky-500/30";
    case "medium":
      return "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30";
    case "low":
      return "bg-zinc-500/15 text-zinc-600 dark:text-zinc-400 border-zinc-500/30";
  }
}

export function placeLine(
  city: string | null | undefined,
  country: string | null | undefined,
): string {
  return [city, country].filter(Boolean).join(", ") || "Location";
}
