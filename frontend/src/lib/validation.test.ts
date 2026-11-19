import { describe, expect, it } from "vitest";
import { ageOn, inspectFile, sniffType, validateDetails, validateIdNumber, wordCount } from "./validation";

const today = new Date("2026-11-19T12:00:00");
const valid = {
  date_of_birth: "1998-04-12",
  phone: "+234 801 234 5678",
  business_idea: Array(30).fill("word").join(" "),
  identification_type: "NIN",
  identification_number: "123 4567 8901",
};

describe("validation", () => {
  it("counts words", () => {
    expect(wordCount("  one two\nthree ")).toBe(3);
    expect(wordCount("   ")).toBe(0);
  });

  it("validates NIN and passport numbers", () => {
    expect(validateIdNumber("NIN", "12345678901")).toBeNull();
    expect(validateIdNumber("NIN", "1234")).toMatch(/11 digits/);
    expect(validateIdNumber("International Passport", "a12345678")).toBeNull();
    expect(validateIdNumber("International Passport", "12345678")).toMatch(/one letter/);
  });

  it("computes age around birthdays", () => {
    expect(ageOn("2008-11-19", today)).toBe(18);
    expect(ageOn("2008-11-20", today)).toBe(17);
  });

  it("accepts a valid application", () => {
    expect(validateDetails(valid, today)).toBeNull();
  });

  it("rejects common problems", () => {
    expect(validateDetails({ ...valid, date_of_birth: "2015-01-01" }, today)).toMatch(/18/);
    expect(validateDetails({ ...valid, phone: "abc" }, today)).toMatch(/phone/);
    expect(validateDetails({ ...valid, business_idea: "too short" }, today)).toMatch(/30 words/);
  });

  it("detects file types from bytes", () => {
    expect(sniffType(new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d, 0x31]))).toBe("application/pdf");
    expect(sniffType(new Uint8Array([0xff, 0xd8, 0xff, 0xe0]))).toBe("image/jpeg");
    expect(sniffType(new Uint8Array([1, 2, 3]))).toBeNull();
  });

  it("inspects files by content, not name", async () => {
    const pdf = new File([new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d, 0x31])], "id.jpg", { type: "image/jpeg" });
    expect(await inspectFile(pdf, "ID", ["application/pdf"])).toEqual({ ok: true, type: "application/pdf" });
    expect(await inspectFile(pdf, "Photo", ["image/jpeg", "image/png"])).toMatchObject({ ok: false });
    expect(await inspectFile(new File([], "x"), "ID", ["application/pdf"])).toMatchObject({ ok: false });
    const big = new File([new Uint8Array(5 * 1024 * 1024 + 1)], "big.pdf");
    expect(await inspectFile(big, "ID", ["application/pdf"])).toMatchObject({ error: "ID must be 5 MB or smaller." });
  });
});
