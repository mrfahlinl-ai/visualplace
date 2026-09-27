import { ThemeToggle } from "@/components/theme-toggle";
import {
  MapPin,
  ScanSearch,
  ShieldCheck,
  Layers,
  Camera,
  Upload,
} from "lucide-react";

const steps = [
  { icon: ScanSearch, label: "Extract visual clues" },
  { icon: Layers, label: "Generate candidates" },
  { icon: MapPin, label: "Verify against maps" },
  { icon: ShieldCheck, label: "Score the evidence" },
];

export default function Home() {
  return (
    <div className="flex min-h-full flex-col">
      {/* Header */}
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <MapPin className="h-4 w-4" aria-hidden />
          </span>
          <span className="text-lg font-semibold tracking-tight">
            VisualPlace
          </span>
        </div>
        <ThemeToggle />
      </header>

      {/* Hero */}
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col items-center px-6">
        <section className="flex flex-col items-center pt-10 text-center sm:pt-16">
          <span className="mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            Evidence-based AI geolocation
          </span>

          <h1 className="max-w-3xl text-balance text-4xl font-semibold tracking-tight sm:text-5xl md:text-6xl">
            Find Where This Photo Was Taken
          </h1>

          <p className="mt-5 max-w-2xl text-pretty text-base text-muted-foreground sm:text-lg">
            Upload an image and let AI analyze landmarks, signs, architecture,
            geography, and other visual clues to identify the most likely
            location — and show you exactly why.
          </p>

          {/* Upload CTA (full uploader arrives in Phase 3) */}
          <div className="mt-10 w-full max-w-xl">
            <div
              className="group flex flex-col items-center gap-4 rounded-2xl border-2 border-dashed border-border bg-card px-6 py-12 text-card-foreground transition-colors hover:border-ring"
              role="button"
              tabIndex={0}
              aria-label="Upload an image to analyze"
            >
              <span className="inline-flex h-14 w-14 items-center justify-center rounded-xl bg-muted text-muted-foreground">
                <Upload className="h-6 w-6" aria-hidden />
              </span>
              <div>
                <p className="font-medium">Drag &amp; drop an image here</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  or browse, paste, or use your camera — JPG, PNG, WEBP, HEIC
                </p>
              </div>
              <div className="mt-2 flex items-center gap-3">
                <button
                  type="button"
                  className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <Upload className="h-4 w-4" aria-hidden />
                  Browse files
                </button>
                <button
                  type="button"
                  className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <Camera className="h-4 w-4" aria-hidden />
                  Camera
                </button>
              </div>
            </div>
            <p className="mt-3 text-center text-xs text-muted-foreground">
              Your photo is processed privately and deleted automatically. We
              never present an uncertain guess as an exact location.
            </p>
          </div>
        </section>

        {/* Pipeline strip */}
        <section className="mt-16 w-full max-w-3xl pb-16">
          <ol className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {steps.map(({ icon: Icon, label }, i) => (
              <li
                key={label}
                className="flex flex-col items-center gap-2 rounded-xl border border-border bg-card px-3 py-4 text-center"
              >
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-muted text-accent">
                  <Icon className="h-4 w-4" aria-hidden />
                </span>
                <span className="text-xs font-medium text-muted-foreground">
                  {i + 1}. {label}
                </span>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <footer className="mx-auto w-full max-w-6xl px-6 py-6 text-center text-xs text-muted-foreground">
        VisualPlace · Transparent, evidence-based location inference
      </footer>
    </div>
  );
}
