import { Notifications } from "@cznethub/cznet-vue-core";
import type { NavigationGuard, RouteLocationRaw } from "vue-router";
import User from "./models/user.model";

export const hasNextRouteGuard: NavigationGuard = () => {
  const nextRoute = User.$state.next;
  if (nextRoute) {
    // Consume the redirect
    User.commit((state) => {
      state.next = "";
    });
    return { path: nextRoute } satisfies RouteLocationRaw;
  }
};

export const hasLoggedInGuard: NavigationGuard = (to, _from, next) => {
  if (!User.$state.isLoggedIn) {
    User.openLogInDialog({ path: to.path });
    next({ name: "home" });
  } else {
    next();
  }
};

export const hasUnsavedChangesGuard: NavigationGuard = (to, _from, next) => {
  if (User.$state.hasUnsavedChanges) {
    Notifications.openDialog({
      title: "You have unsaved changes",
      content: "Do you want to continue and discard your changes?",
      confirmText: "Discard",
      cancelText: "Cancel",
      onConfirm: async () => {
        await User.commit((state) => {
          state.hasUnsavedChanges = false;
        });
        next({ path: to.path });
      },
    });
  } else {
    next();
  }
};
