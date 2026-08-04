import { getNotificationsApp, ZipTask } from "./shared";

export class BagDownloadError extends Error { }

export const requestBag = async (
  bagUrl: string,
): Promise<ZipTask> => {
  const response = await fetch(bagUrl, {
    method: "GET",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      Accept: "application/json",
    },
    credentials: "include",
  });

  if (response.status === 401) {
    throw new BagDownloadError(
      "You do not have permission to download this resource.",
    );
  }
  if (!response.ok) {
    throw new BagDownloadError("Failed to start the bag download.");
  }

  const task = await response.json();
  if (!task?.id || !task?.name) {
    throw new BagDownloadError("Failed to start the bag download.");
  }
  return task;
};

export const downloadBag = async (
  bagUrl: string,
): Promise<void> => {
  const notifications = getNotificationsApp();
  if (!notifications) {
    throw new BagDownloadError("Failed to start the bag download.");
  }

  const task = await requestBag(bagUrl);
  notifications.registerTask(task);
  notifications.show();
};
