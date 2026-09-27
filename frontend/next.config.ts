import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output for lean Docker images (see docker/frontend.Dockerfile).
  output: "standalone",
  reactStrictMode: true,
  // Backend API base is provided at build/run time via env.
  env: {
    NEXT_PUBLIC_API_BASE_URL:
      process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  },
};

export default nextConfig;
