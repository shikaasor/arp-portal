import { describe, expect, it } from "vitest";
import { GEO, LGAS, STATES, wardsFor } from "./options";

describe("location lists (GRID3)", () => {
  it("has every LGA for every state on the form", () => {
    expect(Object.keys(LGAS)).toEqual([...STATES]);
    expect(Object.values(LGAS).flat()).toHaveLength(419);
    expect(LGAS.Kano).toHaveLength(44);
    expect(LGAS.Kano).toContain("Nassarawa");
    expect(LGAS["FCT Abuja"]).toContain("Municipal Area Council");
  });

  it("lists the wards of each LGA", () => {
    const total = STATES.flatMap((s) => LGAS[s].map((l) => wardsFor(s, l).length)).reduce((a, b) => a + b, 0);
    expect(total).toBe(4841);
    expect(wardsFor("Kano", "Nassarawa")).toContain("Gama");
    expect(wardsFor("Kano", "")).toEqual([]);
    expect(wardsFor("", "Nassarawa")).toEqual([]);
  });

  it("carries the GRID3 licence for the credit line", () => {
    expect(GEO.meta.licence).toBe("CC BY-SA 4.0");
  });
});
