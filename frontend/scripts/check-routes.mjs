#!/usr/bin/env node
// Fails if the frontend defines anything under /api, which is reserved for the FastAPI service.
// Catches app-router routes (including inside route groups like `(admin)/api`), pages-router
// API routes, and static files in public/api.
import { existsSync, readdirSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

const root = new URL("..", import.meta.url).pathname;
const RESERVED = "api";
const problems = [];

/** Convert a filesystem path under an app/pages dir to its URL segments. */
function urlSegments(rel) {
  return rel
    .split(sep)
    .filter((s) => s && !(s.startsWith("(") && s.endsWith(")")) && !s.startsWith("@") && !s.startsWith("_"));
}

function walk(dir, base) {
  if (!existsSync(dir)) return;
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    const segs = urlSegments(relative(base, full));
    if (segs[0]?.replace(/\.[^.]+$/, "") === RESERVED) {
      problems.push(relative(root, full));
      continue;
    }
    if (statSync(full).isDirectory()) walk(full, base);
  }
}

for (const dir of ["src/app", "app", "src/pages", "pages", "public"]) walk(join(root, dir), join(root, dir));

if (problems.length) {
  console.error(
    `✖ /${RESERVED}/* is reserved for the FastAPI service (routed by the root vercel.json).\n` +
      `  Move these out of /${RESERVED}:\n` +
      problems.map((p) => `    - ${p}`).join("\n"),
  );
  process.exit(1);
}
console.log(`✓ No frontend routes under /${RESERVED}/ — no clash with the backend.`);
