"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Camera, ImageIcon, Loader2, MapPin, Sparkles, Upload, X } from "lucide-react";
import { createAnalysis } from "@/lib/api";
import { ApiRequestError } from "@/lib/api";
import type { AnalysisMode } from "@/lib/types";
import {
  ACCEPT_ATTR,
  formatBytes,
  readImageDimensions,
  validateFile,
} from "@/lib/upload";
import { cn } from "@/lib/utils";

interface Selected {
  file: File;
  previewUrl: string;
  width: number | null;
  height: number | null;
}

type Phase = "idle" | "ready" | "submitting" | "error";

export function ImageUploader() {
  const router = useRouter();
  const [selected, setSelected] = useState<Selected | null>(null);
  const [dragging, setDragging] = useState(false);
  const [phase, setPhase] = useState<Phase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<AnalysisMode>("identify");
  const [hint, setHint] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const cameraRef = useRef<HTMLInputElement>(null);

  const clear = useCallback(() => {
    setSelected((prev) => {
      if (prev) URL.revokeObjectURL(prev.previewUrl);
      return null;
    });
    setPhase("idle");
    setError(null);
  }, []);

  const accept = useCallback(async (file: File) => {
    const invalid = validateFile(file);
    if (invalid) {
      setError(invalid.message);
      setPhase("error");
      return;
    }
    const dims = await readImageDimensions(file);
    setSelected((prev) => {
      if (prev) URL.revokeObjectURL(prev.previewUrl);
      return {
        file,
        previewUrl: URL.createObjectURL(file),
        width: dims?.width ?? null,
        height: dims?.height ?? null,
      };
    });
    setError(null);
    setPhase("ready");
  }, []);

  // Paste-to-upload.
  useEffect(() => {
    const onPaste = (e: ClipboardEvent) => {
      const file = Array.from(e.clipboardData?.files ?? [])[0];
      if (file) void accept(file);
    };
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, [accept]);

  // Revoke object URL on unmount.
  useEffect(() => {
    return () => {
      if (selected) URL.revokeObjectURL(selected.previewUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) void accept(file);
    },
    [accept],
  );

  const submit = useCallback(async () => {
    if (!selected) return;
    setPhase("submitting");
    setError(null);
    try {
      const res = await createAnalysis(selected.file, {
        mode,
        hint: hint.trim() || undefined,
      });
      // Hand off to the result page, which runs the pipeline and renders it.
      router.push(`/result/${res.id}`);
    } catch (err) {
      const msg =
        err instanceof ApiRequestError
          ? err.message
          : "Couldn't reach the analysis service. Is the backend running?";
      setError(msg);
      setPhase("error");
    }
  }, [selected, mode, hint, router]);

  return (
    <div className="w-full max-w-xl">
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT_ATTR}
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void accept(file);
          e.target.value = "";
        }}
      />
      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void accept(file);
          e.target.value = "";
        }}
      />

      {!selected ? (
        <div
          role="button"
          tabIndex={0}
          aria-label="Upload an image to analyze"
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={cn(
            "flex cursor-pointer flex-col items-center gap-4 rounded-2xl border-2 border-dashed bg-card px-6 py-12 text-card-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            dragging ? "border-ring bg-muted" : "border-border hover:border-ring",
          )}
        >
          <span className="inline-flex h-14 w-14 items-center justify-center rounded-xl bg-muted text-muted-foreground">
            <Upload className="h-6 w-6" aria-hidden />
          </span>
          <div className="text-center">
            <p className="font-medium">Drag &amp; drop an image here</p>
            <p className="mt-1 text-sm text-muted-foreground">
              or browse, paste, or use your camera — JPG, PNG, WEBP, HEIC
            </p>
          </div>
          <div className="mt-2 flex items-center gap-3">
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                inputRef.current?.click();
              }}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Upload className="h-4 w-4" aria-hidden />
              Browse files
            </button>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                cameraRef.current?.click();
              }}
              className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Camera className="h-4 w-4" aria-hidden />
              Camera
            </button>
          </div>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-border bg-card">
          {/* Preview */}
          <div className="relative bg-muted">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={selected.previewUrl}
              alt="Selected upload preview"
              className="max-h-72 w-full object-contain"
            />
            <button
              type="button"
              onClick={clear}
              aria-label="Remove image"
              className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-lg bg-background/80 text-foreground backdrop-blur transition-colors hover:bg-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <X className="h-4 w-4" aria-hidden />
            </button>
          </div>

          {/* Meta */}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-border px-4 py-3 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1.5 font-medium text-foreground">
              <ImageIcon className="h-4 w-4" aria-hidden />
              {selected.file.name}
            </span>
            <span>{formatBytes(selected.file.size)}</span>
            {selected.width && selected.height ? (
              <span>
                {selected.width} × {selected.height}
              </span>
            ) : null}
          </div>

          <div className="space-y-4 p-4">
              {/* Mode */}
              <div className="grid grid-cols-2 gap-2">
                {(
                  [
                    { id: "identify", label: "Identify place", icon: MapPin },
                    { id: "find_exact", label: "Find exact location", icon: Sparkles },
                  ] as const
                ).map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setMode(id)}
                    aria-pressed={mode === id}
                    className={cn(
                      "inline-flex items-center justify-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      mode === id
                        ? "border-primary bg-primary/10 text-foreground"
                        : "border-border text-muted-foreground hover:bg-muted",
                    )}
                  >
                    <Icon className="h-4 w-4" aria-hidden />
                    {label}
                  </button>
                ))}
              </div>

              {/* Hint */}
              <div>
                <label htmlFor="hint" className="text-sm text-muted-foreground">
                  Optional hint (a guess, not treated as fact)
                </label>
                <input
                  id="hint"
                  value={hint}
                  onChange={(e) => setHint(e.target.value)}
                  maxLength={280}
                  placeholder="e.g. Somewhere in Sylhet, Bangladesh"
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>

              {error ? (
                <p className="text-sm text-red-500" role="alert">
                  {error}
                </p>
              ) : null}

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={submit}
                  disabled={phase === "submitting"}
                  className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {phase === "submitting" ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                      Uploading…
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4" aria-hidden />
                      Analyze image
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={clear}
                  className="rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted"
                >
                  Cancel
                </button>
              </div>
            </div>
        </div>
      )}

      <p className="mt-3 text-center text-xs text-muted-foreground">
        Your photo is processed privately and deleted automatically. We never
        present an uncertain guess as an exact location.
      </p>
    </div>
  );
}
