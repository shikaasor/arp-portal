import { describe, expect, it } from "vitest";
import { canReview } from "./review";

describe("canReview", () => {
  it("lets each reviewer act at their own stage", () => {
    expect(canReview("state", { stage: "state_review" })).toBe(true);
    expect(canReview("lga", { stage: "lga_review" })).toBe(true);
    expect(canReview("ward", { stage: "ward_review" })).toBe(true);
    expect(canReview("national", { stage: "ward_review" })).toBe(true);
    expect(canReview("lga", { stage: "state_review" })).toBe(false);
    expect(canReview("national", { stage: "approved" })).toBe(false);
  });

  it("gives the LGA reviewer the ward stage only for an unlisted ward", () => {
    expect(canReview("lga", { stage: "ward_review", ward_unlisted: true })).toBe(true);
    expect(canReview("lga", { stage: "ward_review", ward_unlisted: false })).toBe(false);
    expect(canReview("state", { stage: "ward_review", ward_unlisted: true })).toBe(false);
  });
});
