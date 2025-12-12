import type { RouteLocationRaw } from "vue-router";
import { Notifications } from "@cznethub/cznet-vue-core";
import { Model } from "@vuex-orm/core";
import axios from "axios";

import { Subject } from "rxjs";
import { API_BASE, APP_URL } from "@/constants";

export interface ICzCurrentUserState {
  orcid: string;
  orcidAccessToken: string;
}

export interface IUserState {
  isLoggedIn: boolean;
  orcid: string;
  orcidAccessToken: string;
  next: string;
  hasUnsavedChanges: boolean;
  showZenodoWarning: boolean;
}

export default class User extends Model {
  static entity = "users";
  static logInDialog$ = new Subject<RouteLocationRaw | undefined>();
  static loggedIn$ = new Subject<void>();
  static controller = new AbortController();

  static fields() {
    return {};
  }

  static get $state(): IUserState {
    return this.store().state.entities[this.entity];
  }

  static get next() {}

  static get accessToken() {
    return this.$state?.orcidAccessToken;
  }

  static state(): IUserState {
    return {
      isLoggedIn: false,
      orcid: "",
      orcidAccessToken: "",
      next: "",
      hasUnsavedChanges: false,
      showZenodoWarning: true,
    };
  }

  static openLogInDialog(redirectTo?: RouteLocationRaw) {
    this.logInDialog$.next(redirectTo);
  }

  static async logIn(callback?: () => any) {
    const handleMessage = async (event: MessageEvent) => {
      if (
        event.origin !== APP_URL ||
        !Object.prototype.hasOwnProperty.call(event.data, "token")
      ) {
        console.log(event.origin, APP_URL);
        return;
      }

      if (event.data.token) {
        Notifications.toast({
          message: "You have logged in!",
          type: "info",
        });
        await User.commit((state) => {
          state.isLoggedIn = true;
          state.orcid = event.data.orcid;
          state.orcidAccessToken = event.data.token;
        });
        document.cookie = `Authorization=Bearer ${event.data.token}; expires=${event.data.expiresIn}; path=/`;
        this.controller.abort();
        this.loggedIn$.next();
        callback?.();
      } else {
        Notifications.toast({
          message: "Failed to Log In",
          type: "error",
        });
      }
    };

    window.open(
      `${API_BASE}/login?window_close=True`,
      "_blank",
      "location=1,status=1,scrollbars=1, width=800,height=800",
    );

    this.controller.abort();
    this.controller = new AbortController();
    window.addEventListener("message", handleMessage, {
      signal: this.controller.signal, // Used to remove the listener
    });
    console.info(`[User]: Listening to login window...`);
  }

  static async checkAuthorization() {
    try {
      const response = await axios.get("/api", {
        params: { access_token: User.$state.orcidAccessToken },
      });

      if (response.status !== 200) {
        // Something went wrong, authorization may be invalid
        User.commit((state) => {
          state.isLoggedIn = false;
        });
      }
    } catch (e: any) {
      // console.log(e.response.status)
      User.commit((state) => {
        state.isLoggedIn = false;
      });
    }
  }

  static async logOut() {
    try {
      await axios.get("/api/logout");
      this._logOut();
    } catch (e) {
      // We don't care about the response status. We at least log the user out in the frontend.
      this._logOut();
    }
  }

  private static async _logOut() {
    await User.commit((state) => {
      state.isLoggedIn = false;
      state.orcidAccessToken = "";
    });

    Notifications.toast({
      message: "You have logged out!",
      type: "info",
    });

    // if (useRouter().currentRoute.meta?.hasLoggedInGuard)
    //   useRouter().push({ path: '/' })
  }
}
