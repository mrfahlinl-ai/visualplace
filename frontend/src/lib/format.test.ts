import { describe, expect, it } from "vitest";
import { BAND_META, confidencePercent, placeLine, toneClasses } from "@/lib/format";
import type { ConfidenceBand } from "@/lib/types";

describe("format helpers", () => {
  it("converts confidence to percent", () => {
    expect(confidencePercent(0.874)).toBe(87);
    expect(confidencePercent(null)).toBeNull();
  });

  it("has metadata for every band", () => {
    const bands: ConfidenceBand[] = [
      "exact_gps",
      "strong",
      "probable",
      "approximate",
      "weak",
      "unknown",
    ];
    for (const b of bands) {
      expect(BAND_META[b].label).toBeTruthy();
      expect(toneClasses(BAND_META[b].tone)).toContain("border");
    }
  });

  it("builds a place line and falls back", () => {
    expect(placeLine("Sylhet", "Bangladesh")).toBe("Sylhet, Bangladesh");
    expect(placeLine(null, "Bangladesh")).toBe("Bangladesh");
    expect(placeLine(null, null)).toBe("Location");
  });
});
