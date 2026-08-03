import type { IFile, IFolder } from "@cznethub/cznet-vue-core/dist/types";

const POLL_INTERVAL_MS = 3000;
const POLL_TIMEOUT_MS = 10 * 60 * 1000;

export interface WaitOptions {
  intervalMs?: number;
  timeoutMs?: number;
  now?: () => number;
}

/** Task notification returned by the download endpoint. */
export interface ZipTask {
  id: string;
  name: string;
  status: string;
  payload: string;
}

interface NotificationsApp {
  registerTask: (_task: ZipTask) => void;
  show: () => void;
}

export class ZipDownloadError extends Error { }

/**
 * The navbar task-notification app, which lives on the parent window because
 * the landing page runs in a same-origin iframe.
 */
export const getNotificationsApp = (): NotificationsApp | null => {
  try {
    for (const w of [window.parent, window] as any[]) {
      if (typeof w?.notificationsApp?.registerTask === "function") {
        return w.notificationsApp;
      }
    }
  } catch {
    // cross-origin parent
  }
  return null;
};

export const isFolder = (item: IFile | IFolder): boolean =>
  Object.prototype.hasOwnProperty.call(item, "children");

export const zipRequestUrl = (
  resourceId: string,
  item: IFile | IFolder,
): string => {
  const url = `/django_s3/download/${resourceId}/data/contents/${item.path}`;
  // Folders are zipped server-side automatically; single files need the flag.
  return isFolder(item) ? url : `${url}?zipped=true`;
};

export const requestZip = async (
  resourceId: string,
  item: IFile | IFolder,
): Promise<ZipTask> => {
  const res = await fetch(zipRequestUrl(resourceId, item), {
    credentials: "include",
  });

  if (res.status === 401) {
    throw new ZipDownloadError(
      "You do not have permission to download this resource.",
    );
  }
  if (!res.ok) {
    throw new ZipDownloadError("Failed to start the zip download.");
  }

  const task = await res.json();
  // registerTask ignores anything without both id and name.
  if (!task?.id || !task?.name) {
    throw new ZipDownloadError("Failed to start the zip download.");
  }
  return task;
};

export const waitForZip = async (
  taskId: string,
  opts: WaitOptions = {},
): Promise<string> => {
  const {
    intervalMs = POLL_INTERVAL_MS,
    timeoutMs = POLL_TIMEOUT_MS,
    now = () => Date.now(),
  } = opts;
  const deadline = now() + timeoutMs;

  while (now() < deadline) {
    const res = await fetch(`/django_s3/rest_check_task_status/${taskId}`, {
      credentials: "include",
    });
    if (!res.ok) {
      throw new ZipDownloadError("Failed to create the zip file.");
    }

    const body = await res.json();
    if (body?.status === "true") {
      return body.payload;
    }
    // Anything other than an explicit "still running" is terminal.
    if (body?.status !== "false") {
      throw new ZipDownloadError("Failed to create the zip file.");
    }

    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }

  throw new ZipDownloadError(
    "The zip is taking too long to prepare. Please try again later.",
  );
};

export const triggerDownload = (url: string) => {
  const a = document.createElement("a");
  a.href = url;
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
};

/**
 * Kick off a zipped download. Preferred path hands the task to the navbar
 * notification app, which owns polling and delivery exactly as the legacy
 * landing page does — that keeps the bell in sync and preserves the server's
 * filename. Falls back to polling here when the bell is unreachable.
 */
export const downloadZipped = async (
  resourceId: string,
  item: IFile | IFolder,
  opts: WaitOptions = {},
): Promise<"notified" | "downloaded"> => {
  const task = await requestZip(resourceId, item);

  const notifications = getNotificationsApp();
  if (notifications) {
    notifications.registerTask(task);
    notifications.show();
    return "notified";
  }

  triggerDownload(await waitForZip(task.id, opts));
  return "downloaded";
};
