import { describe, it, expect } from "vitest";
import { pickActiveSection } from "@/components/base/toc-active";

describe("pickActiveSection", () => {
  it("returns an empty string when nothing is at or above the band", () => {
    const offsets = [
      { to: "#details", offsetTop: 400 },
      { to: "#content", offsetTop: 900 },
    ];
    expect(pickActiveSection(offsets, 100)).toBe("");
  });

  it("picks the lowest section still at or above the band", () => {
    const offsets = [
      { to: "#details", offsetTop: 0 },
      { to: "#description", offsetTop: 300 },
      { to: "#content", offsetTop: 900 },
    ];
    expect(pickActiveSection(offsets, 500)).toBe("#description");
  });

  it("includes a section sitting exactly on the band", () => {
    const offsets = [
      { to: "#details", offsetTop: 0 },
      { to: "#content", offsetTop: 500 },
    ];
    expect(pickActiveSection(offsets, 500)).toBe("#content");
  });

  it("picks by position when array order differs from document order", () => {
    // The TOC lists sidebar sections between main-column ones, but at wide
    // widths the sidebar renders alongside rather than below, so a later
    // array entry can sit higher up the page.
    const offsets = [
      { to: "#details", offsetTop: 0 },
      { to: "#subject", offsetTop: 120 },
      { to: "#citation", offsetTop: 340 },
      { to: "#license", offsetTop: 260 },
      { to: "#content", offsetTop: 800 },
    ];
    expect(pickActiveSection(offsets, 400)).toBe("#citation");
  });

  it("keeps the first of two sections at the same position", () => {
    const offsets = [
      { to: "#citation", offsetTop: 200 },
      { to: "#license", offsetTop: 200 },
    ];
    expect(pickActiveSection(offsets, 300)).toBe("#citation");
  });

  it("returns an empty string for an empty list", () => {
    expect(pickActiveSection([], 500)).toBe("");
  });
});
