import type { IFile, IFolder } from "@cznethub/cznet-vue-core/dist/types";
import { getNotificationsApp, type NotificationTask } from "./notifications-app";

export class ZipDownloadError extends Error { }

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
): Promise<NotificationTask> => {
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
