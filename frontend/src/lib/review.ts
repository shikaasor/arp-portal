import type { AdminApplication } from "./api";
import { ROLE_STAGE } from "./options";

export const ACTIVE_STAGES = ["state_review", "lga_review", "ward_review"];

/**
 * Whether a reviewer with `role` can act on `a` (the API checks the same rule).
 * A ward that isn't on the official list can't match a ward reviewer, so the LGA reviewer
 * takes the ward stage for it.
 */
export function canReview(role: string | undefined, a: Pick<AdminApplication, "stage" | "ward_unlisted">): boolean {
  if (!ACTIVE_STAGES.includes(a.stage)) return false;
  if (role === "national" || ROLE_STAGE[role ?? ""] === a.stage) return true;
  return role === "lga" && a.stage === "ward_review" && Boolean(a.ward_unlisted);
}
