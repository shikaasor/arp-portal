import type { NextConfig } from "next";

/**
 * Monorepo routing contract (see docs/DEPLOYMENT.md):
 *   /api/*  → proxied to the FastAPI project (API_ORIGIN). Reserved: the frontend never defines
 *             routes under /api — `npm run check:routes` fails the build if it does.
 *   all else → this Next.js app.
 *
 * API_ORIGIN is server-side only (not exposed to the browser), e.g.
 *   https://arp-portal-api.vercel.app   or   http://localhost:8000 for local dev.
 */
const API_PREFIX = "/api";

function apiOrigin(): string | null {
  const raw = process.env.API_ORIGIN?.trim();
  if (!raw) return null;
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw new Error(`API_ORIGIN must be an absolute URL, got "${raw}"`);
  }
  if (url.pathname !== "/" || url.search) {
    throw new Error(`API_ORIGIN must be an origin only (no path), got "${raw}"`);
  }
  return url.origin;
}

const origin = apiOrigin();

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains; preload" },
];

const nextConfig: NextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  // Tells the browser bundle whether the API proxy is wired up (otherwise: preview mode).
  env: { NEXT_PUBLIC_API_PROXY_ENABLED: origin ? "1" : "" },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  async rewrites() {
    if (!origin) return [];
    // beforeFiles: the API always wins for /api/*, even over files in /public.
    return {
      beforeFiles: [{ source: `${API_PREFIX}/:path*`, destination: `${origin}${API_PREFIX}/:path*` }],
      afterFiles: [],
      fallback: [],
    };
  },
};

export default nextConfig;
