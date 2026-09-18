import { describe, it, expect } from "vitest";
import {
  renderMarkdown,
  isMarkdownFileName,
  toMarkdownFileName,
} from "@/components/landing-page/markdown";

describe("isMarkdownFileName", () => {
  it("recognizes .md regardless of case", () => {
    expect(isMarkdownFileName("README.md")).toBe(true);
    expect(isMarkdownFileName("readme.MD")).toBe(true);
  });

  it("rejects non-markdown names", () => {
    expect(isMarkdownFileName("readme.txt")).toBe(false);
    expect(isMarkdownFileName("notes")).toBe(false);
    expect(isMarkdownFileName("")).toBe(false);
  });
});

describe("toMarkdownFileName", () => {
  it("swaps a trailing .txt for .md, preserving base casing", () => {
    expect(toMarkdownFileName("README.txt")).toBe("README.md");
    expect(toMarkdownFileName("readme.TXT")).toBe("readme.md");
    expect(toMarkdownFileName("My_Readme.txt")).toBe("My_Readme.md");
  });

  it("leaves non-txt names untouched", () => {
    expect(toMarkdownFileName("readme.md")).toBe("readme.md");
    expect(toMarkdownFileName("notes")).toBe("notes");
  });
});

describe("renderMarkdown", () => {
  it("renders markdown to HTML", () => {
    expect(renderMarkdown("# Hi")).toContain("<h1>Hi</h1>");
  });

  it("renders an empty string safely", () => {
    expect(renderMarkdown("")).toBe("");
  });

  it("strips <script> tags (XSS)", () => {
    const out = renderMarkdown("hello\n\n<script>alert(1)</script>");
    expect(out).not.toContain("<script>");
    expect(out).toContain("hello");
  });

  it("strips inline event handlers (XSS)", () => {
    const out = renderMarkdown('<img src=x onerror="alert(1)">');
    expect(out.toLowerCase()).not.toContain("onerror");
  });
});
