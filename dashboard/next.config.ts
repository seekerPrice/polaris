import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Phase-13 hosting prep: reverse-proxy /api/* and /v1/* through Next.js so
  // a single public port (3030) reaches everything. Required for Replit / any
  // single-port hosting where the FastAPI :8000 and Lobster Trap :8080 are
  // NOT externally reachable. The browser hits same-origin URLs; Next.js
  // forwards to loopback inside the container.
  //
  // Local dev: `.env.local` sets NEXT_PUBLIC_API_BASE=http://localhost:8000
  // so the existing direct-fetch path keeps working without going through
  // the proxy (avoids double-hop latency during demo recording).
  //
  // Hosted: NEXT_PUBLIC_API_BASE unset, API_BASE falls back to "" (same-
  // origin), browser fetches /api/policies/packs which lands on Next.js,
  // which rewrites to http://127.0.0.1:8000/api/policies/packs internally.
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://127.0.0.1:8000/api/:path*" },
      { source: "/v1/:path*", destination: "http://127.0.0.1:8080/v1/:path*" },
    ];
  },
};

export default nextConfig;
