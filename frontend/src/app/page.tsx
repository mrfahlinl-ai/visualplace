import { ThemeToggle } from "@/components/theme-toggle";
import { ImageUploader } from "@/components/image-uploader";
import { MapPin, ScanSearch, ShieldCheck, Layers } from "lucide-react";

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

          {/* Upload + analyze */}
          <div className="mt-10 flex w-full justify-center">
            <ImageUploader />
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
