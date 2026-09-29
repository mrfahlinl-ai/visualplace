"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertTriangle, ArrowLeft, MapPin } from "lucide-react";
import { ApiRequestError, getAnalysis, verifyAnalysis } from "@/lib/api";
import type { AnalysisRead } from "@/lib/types";
import { AnalysisProgress } from "@/components/analysis-progress";
import { ResultView } from "@/components/result-view";
import { ThemeToggle } from "@/components/theme-toggle";

type Phase = "loading" | "running" | "done" | "error";

export default function ResultPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [phase, setPhase] = useState<Phase>("loading");
  const [analysis, setAnalysis] = useState<AnalysisRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const started = useRef(false);

  const run = useCallback(async () => {
    try {
      let a = await getAnalysis(id);
      if (a.status === "pending" || a.status === "processing") {
        setPhase("running");
        a = await verifyAnalysis(id);
      }
      setAnalysis(a);
      setPhase("done");
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.message
          : "Couldn't reach the analysis service. Is the backend running?",
      );
      setPhase("error");
    }
  }, [id]);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    void run();
  }, [run]);

  const failed = analysis?.status === "failed";

  return (
    <div className="mx-auto flex min-h-full w-full max-w-4xl flex-col px-6 pb-16">
      <header className="flex items-center justify-between py-5">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden />
          <span className="inline-flex items-center gap-1.5">
            <MapPin className="h-4 w-4 text-primary" aria-hidden />
            VisualPlace
          </span>
        </Link>
        <ThemeToggle />
      </header>

      <main className="flex-1">
        {phase === "loading" || phase === "running" ? (
          <div className="mt-10">
            <AnalysisProgress />
          </div>
        ) : null}

        {phase === "error" || failed ? (
          <div className="mx-auto mt-10 max-w-md rounded-2xl border border-border bg-card p-6 text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-amber-500" aria-hidden />
            <h1 className="mt-3 text-lg font-semibold">We couldn&apos;t complete the analysis</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              {failed
                ? analysis?.error?.message ??
                  "The analysis pipeline reported an error."
                : error}
            </p>
            {analysis?.error?.code === "PROVIDER_NOT_CONFIGURED" ? (
              <p className="mt-2 text-xs text-muted-foreground">
                The AI vision provider isn&apos;t configured on the server
                (missing API key).
              </p>
            ) : null}
            <Link
              href="/"
              className="mt-5 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden />
              Try another image
            </Link>
          </div>
        ) : null}

        {phase === "done" && analysis && !failed ? (
          <ResultView analysis={analysis} />
        ) : null}
      </main>
    </div>
  );
}
