import { describe, expect, it } from "vitest";
import { LGAS, STATES } from "./options";

describe("LGA list", () => {
  it("has the official LGAs for every state on the form", () => {
    expect(Object.keys(LGAS)).toEqual([...STATES]);
    expect(Object.values(LGAS).flat()).toHaveLength(419);
    expect(LGAS.Kano).toHaveLength(44);
    expect(LGAS.Kano).toContain("Nasarawa");
    expect(LGAS["FCT Abuja"]).toContain("Abuja Municipal");
  });
});
