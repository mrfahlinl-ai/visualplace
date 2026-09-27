import { config } from "@/lib/config";
import type { AnalysisMode, AnalysisRead, ApiError } from "@/lib/types";

export class ApiRequestError extends Error {
  code: string;
  status: number;
  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
  }
}

async function parseError(res: Response): Promise<ApiRequestError> {
  try {
    const body = (await res.json()) as ApiError;
    return new ApiRequestError(
      res.status,
      body.error?.code ?? "UNKNOWN",
      body.error?.message ?? res.statusText,
    );
  } catch {
    return new ApiRequestError(res.status, "UNKNOWN", res.statusText);
  }
}

export async function createAnalysis(
  file: File,
  opts: { mode?: AnalysisMode; hint?: string } = {},
): Promise<AnalysisRead> {
  const form = new FormData();
  form.append("file", file);
  form.append("mode", opts.mode ?? "identify");
  if (opts.hint) form.append("hint", opts.hint);

  const res = await fetch(`${config.apiBaseUrl}/api/analyze`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as AnalysisRead;
}

export async function getAnalysis(id: string): Promise<AnalysisRead> {
  const res = await fetch(`${config.apiBaseUrl}/api/analyze/${id}`);
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as AnalysisRead;
}

export async function deleteAnalysis(id: string): Promise<void> {
  const res = await fetch(`${config.apiBaseUrl}/api/analyze/${id}`, {
    method: "DELETE",
  });
  if (!res.ok && res.status !== 404) throw await parseError(res);
}
