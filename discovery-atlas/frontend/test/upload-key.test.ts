import { describe, it, expect } from "vitest";
import { buildUploadKey } from "@/components/landing-page/upload-key";

const prefix = "abc123/data/contents/";

describe("buildUploadKey", () => {
  it("puts a file at the root of the prefix when no folder is given", () => {
    expect(buildUploadKey(prefix, "", "readme.md")).toBe(
      "abc123/data/contents/readme.md",
    );
  });

  it("treats null and undefined folders as the root", () => {
    expect(buildUploadKey(prefix, null, "readme.md")).toBe(
      "abc123/data/contents/readme.md",
    );
    expect(buildUploadKey(prefix, undefined, "readme.md")).toBe(
      "abc123/data/contents/readme.md",
    );
  });

  it("nests the file under the target folder", () => {
    expect(buildUploadKey(prefix, "docs", "readme.md")).toBe(
      "abc123/data/contents/docs/readme.md",
    );
  });

  it("preserves separators in a nested folder path", () => {
    expect(buildUploadKey(prefix, "docs/deep", "readme.md")).toBe(
      "abc123/data/contents/docs/deep/readme.md",
    );
  });

  it("strips stray leading and trailing slashes from the folder", () => {
    expect(buildUploadKey(prefix, "/docs/", "readme.md")).toBe(
      "abc123/data/contents/docs/readme.md",
    );
  });

  it("does not encode the segments; the caller encodes at request time", () => {
    expect(buildUploadKey(prefix, "New folder", "my file.txt")).toBe(
      "abc123/data/contents/New folder/my file.txt",
    );
  });

  it("works with an empty prefix", () => {
    expect(buildUploadKey("", "docs", "readme.md")).toBe("docs/readme.md");
  });
});
