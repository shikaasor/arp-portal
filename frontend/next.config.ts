import { existsSync } from "node:fs";
import { resolve } from "node:path";
import type { NextConfig } from "next";

// One env file for the whole repo: the root `.env.local` (see `.env.example`), shared with the
// API. Next.js only reads env files from `frontend/`, so load the root one here. Values that
// are already set (real environment, or a `frontend/.env*` file) are not overwritten.
const rootEnvFile = resolve(process.cwd(), "..", ".env.local");
if (existsSync(rootEnvFile)) process.loadEnvFile(rootEnvFile);

/**
 * Routing contract (see docs/DEPLOYMENT.md):
 *   /api/*  → the FastAPI service. Reserved: the frontend never defines routes under /api —
 *             `npm run check:routes` fails the build if it does.
 *   all else → this Next.js app.
 *
 * On Vercel, the root vercel.json sends /api/* to the FastAPI service before requests reach
 * Next.js, so no proxy is needed there. API_ORIGIN is only for running outside Vercel's
 * Services routing (e.g. `next dev` + uvicorn on :8000, or self-hosting): when set, Next.js
 * proxies /api/* to it. Server-side only, e.g. http://localhost:8000.
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
// Vercel sets VERCEL=1 at build time; there the API service shares this deployment's domain.
const apiEnabled = Boolean(origin) || process.env.VERCEL === "1";

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
  // Tells the browser bundle whether /api/* is served (otherwise: preview mode).
  env: { NEXT_PUBLIC_API_ENABLED: apiEnabled ? "1" : "" },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  async rewrites() {
    if (!origin) return [];
    // Outside Vercel only. beforeFiles: the API always wins for /api/*, even over /public.
    return {
      beforeFiles: [{ source: `${API_PREFIX}/:path*`, destination: `${origin}${API_PREFIX}/:path*` }],
      afterFiles: [],
      fallback: [],
    };
  },
};

export default nextConfig;
