/** Task notification handed to the navbar notification app. */
export interface NotificationTask {
  id: string;
  name: string;
  status: string;
  payload: string;
}

interface NotificationsApp {
  registerTask: (_task: NotificationTask) => void;
  show: () => void;
}

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
