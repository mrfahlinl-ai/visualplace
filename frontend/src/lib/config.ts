/** Client-safe runtime config. Only NEXT_PUBLIC_* values belong here. */
export const config = {
  apiBaseUrl:
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  mapProvider: process.env.NEXT_PUBLIC_MAP_PROVIDER ?? "osm",
  mapPublicKey: process.env.NEXT_PUBLIC_MAP_KEY ?? "",
} as const;
