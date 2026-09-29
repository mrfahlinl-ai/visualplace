"use client";

import { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";

const STAGES = [
  "Image processed",
  "EXIF metadata checked",
  "Visual clues extracted",
  "Identifying landmarks",
  "Searching places",
  "Comparing candidates",
  "Verifying result",
];

/** Indeterminate staged progress shown while the pipeline runs (spec §6). */
export function AnalysisProgress() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const t = setInterval(() => {
      setActive((a) => Math.min(a + 1, STAGES.length - 1));
    }, 900);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="mx-auto w-full max-w-md rounded-2xl border border-border bg-card p-6">
      <div className="mb-4 flex items-center gap-2 font-medium">
        <Loader2 className="h-4 w-4 animate-spin text-primary" aria-hidden />
        Analyzing image
      </div>
      <ol className="space-y-2.5" aria-live="polite">
        {STAGES.map((stage, i) => {
          const done = i < active;
          const current = i === active;
          return (
            <li
              key={stage}
              className={`flex items-center gap-3 text-sm ${
                done || current ? "text-foreground" : "text-muted-foreground"
              }`}
            >
              <span
                className={`inline-flex h-5 w-5 items-center justify-center rounded-full border ${
                  done
                    ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-500"
                    : current
                      ? "border-primary/40 bg-primary/15 text-primary"
                      : "border-border"
                }`}
              >
                {done ? (
                  <Check className="h-3 w-3" aria-hidden />
                ) : current ? (
                  <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
                ) : null}
              </span>
              {stage}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
