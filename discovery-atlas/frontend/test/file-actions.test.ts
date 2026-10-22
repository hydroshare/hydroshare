import { afterEach, describe, it, expect, vi } from "vitest";
import {
  FileActionError,
  addReferenceAction,
  addReferenceContent,
  fileUrl,
  getFileUrlAction,
  isFileOverrideFailure,
  isTaskSuccessful,
  isZipFile,
  requestUnzip,
  taskFailureMessage,
  unzipActions,
  waitForTask,
} from "@/components/landing-page/file-actions";

const zip = { name: "Data.ZIP", file: null, isUploaded: true, key: 1, path: "top/Data.ZIP" } as any;
const txt = { name: "a.txt", file: null, isUploaded: true, key: 2, path: "a.txt" } as any;
const folder = { name: "f.zip", children: [], key: 3, path: "f.zip" } as any;
const root = { name: "", children: [] } as any;
const ctx = { folder: root, folderPath: "docs", source: "toolbar" } as any;

const res = (body: any, ok = true, status = 200) => ({
  ok,
  status,
  json: async () => body,
  text: async () => (typeof body === "string" ? body : JSON.stringify(body)),
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("fileUrl", () => {
  it("matches the legacy file URL, encoding each segment", () => {
    expect(fileUrl("https://hs.org", "abc", "New folder/a b.txt")).toBe(
      "https://hs.org/resource/abc/data/contents/New%20folder/a%20b.txt",
    );
  });
});

describe("isZipFile", () => {
  it("accepts uploaded zip files in any case", () => {
    expect(isZipFile(zip)).toBe(true);
  });

  it("rejects other files, folders and staged files", () => {
    expect(isZipFile(txt)).toBe(false);
    expect(isZipFile(folder)).toBe(false);
    expect(isZipFile({ ...zip, isUploaded: false })).toBe(false);
  });
});

describe("requestUnzip", () => {
  it("posts the legacy parameters as an ajax request and returns the task", async () => {
    const fetchMock = vi.fn(async (_url: string, _opts: RequestInit) =>
      res({ id: "t1", name: "file unzip", status: "progress", payload: "" }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      requestUnzip("abc", "top/Data.ZIP", { toFolder: true, overwrite: false, csrfToken: "tok" }),
    ).resolves.toMatchObject({ id: "t1" });

    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toBe("/hsapi/_internal/data-store-folder-unzip/");
    expect(opts.headers).toMatchObject({
      "X-CSRFToken": "tok",
      "X-Requested-With": "XMLHttpRequest",
    });
    const body = new URLSearchParams(opts.body as string);
    expect(Object.fromEntries(body)).toEqual({
      res_id: "abc",
      zip_with_rel_path: "top/Data.ZIP",
      remove_original_zip: "false",
      overwrite: "false",
      unzip_to_folder: "true",
    });
  });

  it("surfaces the server error", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => res({ error: "Permission denied" }, false, 401)));
    await expect(
      requestUnzip("abc", "a.zip", { toFolder: false, overwrite: false, csrfToken: null }),
    ).rejects.toThrow("Permission denied");
  });

  it("fails without a task id", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => res({})));
    await expect(
      requestUnzip("abc", "a.zip", { toFolder: false, overwrite: false, csrfToken: null }),
    ).rejects.toThrow(FileActionError);
  });
});

describe("waitForTask", () => {
  it("polls until the task leaves progress and keeps the original name", async () => {
    vi.useFakeTimers();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(res({ id: "t1", name: "", status: "progress", payload: "" }))
      .mockResolvedValueOnce(res({ id: "t1", name: "", status: "completed", payload: "/r" }));
    vi.stubGlobal("fetch", fetchMock);

    const pending = waitForTask(
      { id: "t1", name: "file unzip", status: "progress", payload: "" },
      { intervalMs: 10 },
    );
    await vi.advanceTimersByTimeAsync(50);

    await expect(pending).resolves.toMatchObject({ status: "completed", name: "file unzip" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[0][0]).toBe("/hsapi/_internal/get_task/t1");
  });

  it("returns immediately for a finished task", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const task = { id: "t1", name: "file unzip", status: "failed", payload: "x" };
    await expect(waitForTask(task)).resolves.toBe(task);
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("task status helpers", () => {
  it("treats completed and delivered as success", () => {
    expect(isTaskSuccessful({ id: "", name: "", status: "completed", payload: "" })).toBe(true);
    expect(isTaskSuccessful({ id: "", name: "", status: "delivered", payload: "" })).toBe(true);
    expect(isTaskSuccessful({ id: "", name: "", status: "failed", payload: "" })).toBe(false);
  });

  it("detects a file override failure and extracts its message", () => {
    const payload =
      "FileOverrideException(FileOverrideException(...), 'resource files already exist')";
    const task = { id: "", name: "", status: "failed", payload };
    expect(isFileOverrideFailure(task)).toBe(true);
    expect(taskFailureMessage(payload)).toBe("Resource files already exist");
  });
});

describe("addReferenceContent", () => {
  it("posts the legacy parameters", async () => {
    const fetchMock = vi.fn(async (_url: string, _opts: RequestInit) =>
      res({ status: "success", file_id: 1 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      addReferenceContent("abc", "docs", "Site", "https://x.org", true, "tok"),
    ).resolves.toEqual({ ok: true, message: "" });

    const [url, opts] = fetchMock.mock.calls[0];
    expect(url).toBe("/hsapi/_internal/data-store-add-reference/");
    expect(Object.fromEntries(new URLSearchParams(opts.body as string))).toEqual({
      res_id: "abc",
      curr_path: "docs",
      ref_name: "Site",
      ref_url: "https://x.org",
      validate_url_flag: "true",
    });
  });

  it("returns the server message on failure", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => res({ message: "Invalid URL" }, false, 400)));
    await expect(
      addReferenceContent("abc", "", "Site", "bad", true, null),
    ).resolves.toEqual({ ok: false, message: "Invalid URL" });
  });

  it("reads plain text errors", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => res("Must have ref_url", false, 400)));
    await expect(
      addReferenceContent("abc", "", "Site", "", true, null),
    ).resolves.toEqual({ ok: false, message: "Must have ref_url" });
  });
});

describe("explorer actions", () => {
  it("offers Get file URL for exactly one uploaded item", () => {
    const open = vi.fn();
    const action = getFileUrlAction(open);
    expect(action.isEnabled!([txt], ctx)).toBe(true);
    expect(action.isEnabled!([folder], ctx)).toBe(true);
    expect(action.isEnabled!([txt, zip], ctx)).toBe(false);
    expect(action.isEnabled!([], ctx)).toBe(false);
    action.handler([txt], ctx);
    expect(open).toHaveBeenCalledWith(txt);
  });

  it("offers both unzip actions for a single zip file only", async () => {
    const unzip = vi.fn(async () => {});
    const [here, toFolder] = unzipActions(unzip);
    expect(here.isEnabled!([zip], ctx)).toBe(true);
    expect(here.isEnabled!([txt], ctx)).toBe(false);
    expect(toFolder.isEnabled!([zip, zip], ctx)).toBe(false);

    await here.handler([zip], ctx);
    await toFolder.handler([zip], ctx);
    expect(unzip).toHaveBeenNthCalledWith(1, zip, false);
    expect(unzip).toHaveBeenNthCalledWith(2, zip, true);
  });

  it("opens the reference dialog for the target folder", () => {
    const open = vi.fn();
    const action = addReferenceAction(open);
    expect(action.isEnabled).toBeUndefined();
    action.handler([], ctx);
    expect(open).toHaveBeenCalledWith(root, "docs");
  });
});
