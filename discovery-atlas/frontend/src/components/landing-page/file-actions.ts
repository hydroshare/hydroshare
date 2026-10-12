import type {
  IFile,
  IFileExplorerAction,
  IFolder,
} from "@cznethub/cznet-vue-core/dist/types";
import type { NotificationTask } from "./notifications-app";
import { isFolder } from "./zip-download";

export class FileActionError extends Error { }

const encodePath = (path: string): string =>
  path.split("/").filter(Boolean).map(encodeURIComponent).join("/");

/** Same shape as the legacy file browser's "Get file URL": `<origin>/resource/<id>/data/contents/<path>`. */
export const fileUrl = (origin: string, resourceId: string, path: string): string =>
  `${origin}/resource/${resourceId}/data/contents/${encodePath(path)}`;

export const isZipFile = (item: IFile | IFolder): boolean =>
  !isFolder(item) &&
  item.isUploaded !== false &&
  item.name.toLowerCase().endsWith(".zip");

const postForm = async (
  url: string,
  body: Record<string, string>,
  csrfToken: string | null,
  extraHeaders: Record<string, string> = {},
): Promise<Response> =>
  fetch(url, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      ...(csrfToken ? { "X-CSRFToken": csrfToken } : {}),
      ...extraHeaders,
    },
    body: new URLSearchParams(body).toString(),
  });

/** Reads `error` or `message` from a JSON error body, falling back to the raw text. */
const readErrorMessage = async (res: Response, fallback: string): Promise<string> => {
  try {
    const text = await res.text();
    try {
      const body = JSON.parse(text);
      return body?.error || body?.message || fallback;
    } catch {
      return text || fallback;
    }
  } catch {
    return fallback;
  }
};

export interface UnzipOptions {
  toFolder: boolean;
  overwrite: boolean;
  csrfToken: string | null;
}

/**
 * Queues an unzip on the server. The XMLHttpRequest header makes the view run
 * it as a background task and return its notification, as the legacy page does.
 */
export const requestUnzip = async (
  resourceId: string,
  zipPath: string,
  { toFolder, overwrite, csrfToken }: UnzipOptions,
): Promise<NotificationTask> => {
  const res = await postForm(
    "/hsapi/_internal/data-store-folder-unzip/",
    {
      res_id: resourceId,
      zip_with_rel_path: zipPath,
      remove_original_zip: "false",
      overwrite: String(overwrite),
      unzip_to_folder: String(toFolder),
    },
    csrfToken,
    { "X-Requested-With": "XMLHttpRequest" },
  );

  if (!res.ok) {
    throw new FileActionError(await readErrorMessage(res, "Failed to start unzipping."));
  }

  const task = await res.json();
  if (!task?.id) {
    throw new FileActionError("Failed to start unzipping.");
  }
  return task;
};

export const isTaskFinished = (task: NotificationTask): boolean =>
  task.status !== "progress";

export const isTaskSuccessful = (task: NotificationTask): boolean =>
  task.status === "completed" || task.status === "delivered";

export const isFileOverrideFailure = (task: NotificationTask): boolean =>
  task.status === "failed" && !!task.payload?.includes("FileOverrideException");

/** Pulls the human-readable part out of a stringified exception, like the legacy bell does. */
export const taskFailureMessage = (payload: string): string => {
  const start = payload.indexOf("'");
  if (start >= 0) {
    const end = payload.indexOf("'", start + 1);
    if (end > 0) {
      const message = payload.slice(start + 1, end);
      return message.charAt(0).toUpperCase() + message.slice(1);
    }
  }
  return payload;
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** Polls a task until it leaves `progress` or `timeoutMs` elapses; returns the last state seen. */
export const waitForTask = async (
  task: NotificationTask,
  { intervalMs = 3000, timeoutMs = 30 * 60 * 1000 } = {},
): Promise<NotificationTask> => {
  let current = task;
  const deadline = Date.now() + timeoutMs;
  while (!isTaskFinished(current) && Date.now() < deadline) {
    await sleep(intervalMs);
    try {
      const res = await fetch(`/hsapi/_internal/get_task/${task.id}`, {
        credentials: "include",
      });
      if (res.ok) {
        current = { ...current, ...(await res.json()), name: task.name };
      }
    } catch {
      // transient network error; keep polling
    }
  }
  return current;
};

export interface AddReferenceResult {
  ok: boolean;
  message: string;
}

/** Creates a `.url` file in `folderPath` pointing at `refUrl`. */
export const addReferenceContent = async (
  resourceId: string,
  folderPath: string,
  name: string,
  refUrl: string,
  validateUrl: boolean,
  csrfToken: string | null,
): Promise<AddReferenceResult> => {
  const res = await postForm(
    "/hsapi/_internal/data-store-add-reference/",
    {
      res_id: resourceId,
      curr_path: folderPath,
      ref_name: name,
      ref_url: refUrl,
      validate_url_flag: String(validateUrl),
    },
    csrfToken,
  );

  if (res.ok) {
    return { ok: true, message: "" };
  }
  return {
    ok: false,
    message: await readErrorMessage(res, "Failed to add reference content."),
  };
};

export const getFileUrlAction = (
  open: (_item: IFile | IFolder) => void,
): IFileExplorerAction => ({
  key: "get-file-url",
  label: "Get file URL",
  icon: "mdi-link-variant",
  color: "blue",
  isEnabled: (items) => items.length === 1 && items[0].isUploaded !== false,
  handler: (items) => open(items[0]),
});

export const unzipActions = (
  unzip: (_item: IFile, _toFolder: boolean) => Promise<void>,
): IFileExplorerAction[] => {
  const isEnabled = (items: (IFile | IFolder)[]) =>
    items.length === 1 && isZipFile(items[0]);
  return [
    {
      key: "unzip-here",
      label: "Unzip here",
      icon: "mdi-archive-arrow-down-outline",
      isEnabled,
      handler: (items) => unzip(items[0] as IFile, false),
    },
    {
      key: "unzip-to-folder",
      label: "Unzip to folder",
      icon: "mdi-folder-zip-outline",
      isEnabled,
      handler: (items) => unzip(items[0] as IFile, true),
    },
  ];
};

export const addReferenceAction = (
  open: (_folder: IFolder, _folderPath: string) => void,
): IFileExplorerAction => ({
  key: "add-reference",
  label: "Add content from the web",
  icon: "mdi-link-plus",
  handler: (_items, context) => open(context.folder, context.folderPath),
});
