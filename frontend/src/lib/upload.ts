/** Client-side upload constraints (mirror the backend; the server re-validates). */

export const MAX_UPLOAD_BYTES = Number(
  process.env.NEXT_PUBLIC_MAX_UPLOAD_BYTES ?? 15 * 1024 * 1024,
);

export const ALLOWED_MIME = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/heic",
  "image/heif",
]);

export const ACCEPT_ATTR = ".jpg,.jpeg,.png,.webp,.heic,.heif,image/*";

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export interface FileValidationError {
  code: "TYPE" | "SIZE";
  message: string;
}

export function validateFile(file: File): FileValidationError | null {
  const typeOk =
    ALLOWED_MIME.has(file.type) || /\.(jpe?g|png|webp|heic|heif)$/i.test(file.name);
  if (!typeOk) {
    return { code: "TYPE", message: "Unsupported file type. Use JPG, PNG, WEBP or HEIC." };
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return {
      code: "SIZE",
      message: `Image is too large (max ${formatBytes(MAX_UPLOAD_BYTES)}).`,
    };
  }
  return null;
}

/** Read pixel dimensions in the browser (best-effort; HEIC may not decode). */
export function readImageDimensions(
  file: File,
): Promise<{ width: number; height: number } | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      resolve({ width: img.naturalWidth, height: img.naturalHeight });
      URL.revokeObjectURL(url);
    };
    img.onerror = () => {
      resolve(null);
      URL.revokeObjectURL(url);
    };
    img.src = url;
  });
}
