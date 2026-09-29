import { describe, expect, it } from "vitest";
import { formatBytes, validateFile } from "@/lib/upload";

function file(name: string, type: string, size: number): File {
  const f = new File([new Uint8Array(1)], name, { type });
  Object.defineProperty(f, "size", { value: size });
  return f;
}

describe("upload validation", () => {
  it("formats bytes", () => {
    expect(formatBytes(512)).toBe("512 B");
    expect(formatBytes(2048)).toBe("2 KB");
    expect(formatBytes(3 * 1024 * 1024)).toBe("3.0 MB");
  });

  it("accepts a valid image", () => {
    expect(validateFile(file("p.png", "image/png", 1000))).toBeNull();
  });

  it("rejects unsupported types", () => {
    const err = validateFile(file("doc.pdf", "application/pdf", 1000));
    expect(err?.code).toBe("TYPE");
  });

  it("accepts by extension when type is blank", () => {
    expect(validateFile(file("photo.HEIC", "", 1000))).toBeNull();
  });

  it("rejects oversized files", () => {
    const err = validateFile(file("big.jpg", "image/jpeg", 999 * 1024 * 1024));
    expect(err?.code).toBe("SIZE");
  });
});
