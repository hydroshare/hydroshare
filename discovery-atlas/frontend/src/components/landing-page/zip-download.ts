import type { IFile, IFolder } from "@cznethub/cznet-vue-core/dist/types";

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

/**
 * Kick off a zipped download. The navbar notification app owns polling and
 * delivery, exactly as the legacy landing page does — that keeps the bell in
 * sync and preserves the server's filename.
 */
export const downloadZipped = async (
  resourceId: string,
  item: IFile | IFolder,
): Promise<void> => {
  const notifications = getNotificationsApp();
  if (!notifications) {
    throw new ZipDownloadError("Failed to start the zip download.");
  }

  const task = await requestZip(resourceId, item);
  notifications.registerTask(task);
  notifications.show();
};
