import { describe, it, expect, vi } from "vitest";
import {
  ZipDownloadError,
  isFolder,
  zipRequestUrl,
  requestZip,
  waitForZip,
  downloadZipped,
  getNotificationsApp,
} from "@/components/landing-page/zip-download";

const folder = { name: "f", children: [], key: 1, path: "top/f" } as any;
const file = { name: "a.txt", file: null, isUploaded: true, key: 2, path: "top/a.txt" } as any;

const jsonRes = (body: any, ok = true, status = 200) => ({
  ok,
  status,
  json: async () => body,
});

describe("isFolder", () => {
  it("distinguishes folders from files by the children property", () => {
    expect(isFolder(folder)).toBe(true);
    expect(isFolder(file)).toBe(false);
  });
});

describe("zipRequestUrl", () => {
  it("omits zipped=true for folders, which the server zips automatically", () => {
    expect(zipRequestUrl("abc", folder)).toBe(
      "/django_s3/download/abc/data/contents/top/f",
    );
  });

  it("adds zipped=true for single files", () => {
    expect(zipRequestUrl("abc", file)).toBe(
      "/django_s3/download/abc/data/contents/top/a.txt?zipped=true",
    );
  });
});

describe("requestZip", () => {
  it("sends cookies and returns the task notification", async () => {
    const fetchMock = vi.fn(async (_url: string, _opts: RequestInit) =>
      jsonRes({ id: "task-1", name: "zip download", status: "progress", payload: "" }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(requestZip("abc", folder)).resolves.toMatchObject({
      id: "task-1",
      name: "zip download",
    });

    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toBe("/django_s3/download/abc/data/contents/top/f");
    expect(opts).toMatchObject({ credentials: "include" });

    vi.unstubAllGlobals();
  });

  it("reports a permission problem on 401", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonRes({}, false, 401)));
    await expect(requestZip("abc", folder)).rejects.toThrow(/permission/i);
    vi.unstubAllGlobals();
  });

  it("fails when the response carries no task id", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonRes({ status: "progress" })));
    await expect(requestZip("abc", folder)).rejects.toThrow(ZipDownloadError);
    vi.unstubAllGlobals();
  });

  it("fails when the response has no name, which registerTask requires", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonRes({ id: "task-1" })));
    await expect(requestZip("abc", folder)).rejects.toThrow(ZipDownloadError);
    vi.unstubAllGlobals();
  });
});

describe("waitForZip", () => {
  it("polls until the task reports ready and returns the payload", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonRes({ status: "false" }))
      .mockResolvedValueOnce(jsonRes({ status: "false" }))
      .mockResolvedValueOnce(
        jsonRes({ status: "true", payload: "/django_s3/rest_download/zips/x.zip" }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(waitForZip("task-1", { intervalMs: 0 })).resolves.toBe(
      "/django_s3/rest_download/zips/x.zip",
    );
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[0][0]).toBe(
      "/django_s3/rest_check_task_status/task-1",
    );

    vi.unstubAllGlobals();
  });

  it("fails on a 500 from the status endpoint", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonRes({ status: "false" }, false, 500)));
    await expect(waitForZip("task-1", { intervalMs: 0 })).rejects.toThrow(
      ZipDownloadError,
    );
    vi.unstubAllGlobals();
  });

  it("fails instead of polling forever when the notification is missing", async () => {
    const fetchMock = vi.fn(async () => jsonRes({ status: null }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(waitForZip("task-1", { intervalMs: 0 })).rejects.toThrow(
      ZipDownloadError,
    );
    expect(fetchMock).toHaveBeenCalledTimes(1);

    vi.unstubAllGlobals();
  });

  it("gives up once the deadline passes", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonRes({ status: "false" })));
    let t = 0;
    const now = () => (t += 60_000);

    await expect(
      waitForZip("task-1", { intervalMs: 0, timeoutMs: 120_000, now }),
    ).rejects.toThrow(/too long/i);

    vi.unstubAllGlobals();
  });
});

const startedTask = {
  id: "task-1",
  name: "zip download",
  status: "progress",
  payload: "/dl",
};

describe("downloadZipped", () => {
  it("hands the task to the navbar bell and does not poll or download itself", async () => {
    const fetchMock = vi.fn(async () => jsonRes(startedTask));
    vi.stubGlobal("fetch", fetchMock);
    const registerTask = vi.fn();
    const show = vi.fn();
    vi.stubGlobal("notificationsApp", { registerTask, show });

    await expect(downloadZipped("abc", folder)).resolves.toBe("notified");

    expect(registerTask).toHaveBeenCalledWith(
      expect.objectContaining({ id: "task-1", name: "zip download" }),
    );
    expect(show).toHaveBeenCalledOnce();
    // Only the initial request — the bell owns polling and delivery.
    expect(fetchMock).toHaveBeenCalledTimes(1);

    vi.unstubAllGlobals();
  });

  it("falls back to polling and delivering itself when the bell is unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(jsonRes(startedTask))
        .mockResolvedValueOnce(jsonRes({ status: "true", payload: "/zip/url" })),
    );
    const click = vi.fn();
    const created = document.createElement("a");
    created.click = click;
    vi.spyOn(document, "createElement").mockReturnValueOnce(created as any);

    await expect(downloadZipped("abc", folder, { intervalMs: 0 })).resolves.toBe(
      "downloaded",
    );

    expect(click).toHaveBeenCalledOnce();
    expect(created.getAttribute("href")).toBe("/zip/url");
    expect(document.body.contains(created)).toBe(false);

    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });
});

describe("getNotificationsApp", () => {
  it("returns null when no notification app is present", () => {
    expect(getNotificationsApp()).toBeNull();
  });

  it("ignores a global that lacks registerTask", () => {
    vi.stubGlobal("notificationsApp", { show: () => {} });
    expect(getNotificationsApp()).toBeNull();
    vi.unstubAllGlobals();
  });
});
