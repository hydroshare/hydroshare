import { describe, it, expect, vi } from "vitest";
import {
  PutObjectCommand,
  DeleteObjectCommand,
} from "@aws-sdk/client-s3";
import {
  readmeKey,
  loadReadme,
  saveReadme,
  convertReadmeToMarkdown,
} from "@/components/landing-page/readme-s3";

// Mock just needs to record the commands sent.
function makeClient() {
  return { send: vi.fn(async () => ({})) } as any;
}

const sent = (client: any) => client.send.mock.calls.map((c: any[]) => c[0]);

describe("readmeKey", () => {
  it("builds the contents path", () => {
    expect(readmeKey("abc", "README.md")).toBe("abc/data/contents/README.md");
  });
});

describe("loadReadme", () => {
  it("fetches the object with cache bypass and returns the body text", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      text: async () => "# Title",
    }));
    vi.stubGlobal("fetch", fetchMock);

    const text = await loadReadme("bucket", "abc", "README.md");
    expect(text).toBe("# Title");

    const [url, opts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/bucket/abc/data/contents/README.md");
    expect(url).toMatch(/[?&]_=\d+/); // unique cache-buster
    expect(opts).toMatchObject({ credentials: "include", cache: "no-store" });

    vi.unstubAllGlobals();
  });

  it("throws on a non-ok response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({ ok: false, status: 404 })),
    );
    await expect(loadReadme("bucket", "abc", "README.md")).rejects.toThrow(
      /HTTP 404/,
    );
    vi.unstubAllGlobals();
  });
});

describe("saveReadme", () => {
  it("PUTs in place with markdown content type and returns byte size", async () => {
    const client = makeClient();
    const size = await saveReadme(client, "bucket", "abc", "README.md", "hi");

    const put = sent(client)[0];
    expect(put).toBeInstanceOf(PutObjectCommand);
    expect(put.input.Key).toBe("abc/data/contents/README.md");
    expect(put.input.Body).toBe("hi");
    expect(put.input.ContentType).toBe("text/markdown");
    expect(size).toBe(2);
    // No delete on an in-place save.
    expect(sent(client).some((c: any) => c instanceof DeleteObjectCommand)).toBe(
      false,
    );
  });

  it("uses text/plain for a .txt file", async () => {
    const client = makeClient();
    await saveReadme(client, "bucket", "abc", "README.txt", "notes");
    expect(sent(client)[0].input.ContentType).toBe("text/plain");
  });

  it("counts multi-byte characters correctly", async () => {
    const client = makeClient();
    // "é" is 2 bytes in UTF-8.
    const size = await saveReadme(client, "bucket", "abc", "README.md", "é");
    expect(size).toBe(2);
  });
});

describe("convertReadmeToMarkdown", () => {
  it("writes the .md then deletes the .txt, preserving base casing", async () => {
    const client = makeClient();
    const result = await convertReadmeToMarkdown(
      client,
      "bucket",
      "abc",
      "README.txt",
      "plain notes",
    );

    const cmds = sent(client);
    const put = cmds.find((c: any) => c instanceof PutObjectCommand);
    const del = cmds.find((c: any) => c instanceof DeleteObjectCommand);

    expect(put.input.Key).toBe("abc/data/contents/README.md");
    expect(put.input.Body).toBe("plain notes");
    expect(put.input.ContentType).toBe("text/markdown");
    expect(del.input.Key).toBe("abc/data/contents/README.txt");

    // PUT before DELETE.
    expect(cmds.indexOf(put)).toBeLessThan(cmds.indexOf(del));

    expect(result).toEqual({ name: "README.md", size: 11 });
  });
});
