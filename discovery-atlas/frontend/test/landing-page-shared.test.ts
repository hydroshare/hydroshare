import { describe, it, expect, vi } from "vitest";
import { readRootFolder } from "@/components/landing-page/shared";

function makeClient() {
  return {
    send: vi.fn()
      .mockResolvedValueOnce({
        Contents: [
          { Key: "abc/data/contents/visible.txt", Size: 10 },
          { Key: "abc/data/contents/resourcemap.xml", Size: 10 },
          { Key: "abc/data/contents/test_meta.xml", Size: 11 },
          { Key: "abc/data/contents/test_resmap.xml", Size: 12 },
          { Key: "abc/data/contents/hs_user_metadata.json", Size: 13 },
          { Key: "abc/data/contents/test_schema.json", Size: 14 },
          { Key: "abc/data/contents/test_schema_values.json", Size: 15 },
        ],
        CommonPrefixes: [{ Prefix: "abc/data/contents/folder1/" }],
      })
      .mockResolvedValueOnce({
        Contents: [
          { Key: "abc/data/contents/folder1/child.csv", Size: 20 },
          { Key: "abc/data/contents/folder1/child_meta.xml", Size: 21 },
          { Key: "abc/data/contents/folder1/child_resmap.xml", Size: 22 },
        ],
        CommonPrefixes: [],
      }),
  } as any;
}

describe("readRootFolder", () => {
  it("prunes metadata sidecar files from the recursive S3 tree", async () => {
    const client = makeClient();
    const tree = await readRootFolder("abc/data/contents/", client, "bucket");

    expect(tree.map((item: any) => item.name)).toEqual([
      "folder1",
      "resourcemap.xml",
      "visible.txt",
    ]);

    const folder = tree.find((item: any) => item.name === "folder1") as any;
    expect(folder.children.map((item: any) => item.name)).toEqual(["child.csv"]);
  });
});