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
  toc: { to: string; text: string; level?: number }[];
  isTocReady: boolean;
  CSRFToken: string;
}

export enum PrivilegeCodes {
  OWNER = 1,
  CHANGE = 2,
  VIEW = 3,
  NONE = 4,
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
      toc: [],
      isTocReady: false,
      CSRFToken: "",
    };
  }

  static async checkLoginStatus() {
    try {
      const response = await fetch(`/hsapi/userInfo/`, {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        await User.commit((state) => {
          state.isLoggedIn = true;
          state.orcid = data.orcid || data.username || "";
        });
        return true;
      }
    } catch (e) {
      // network error
    }

    User.commit((state) => {
      state.isLoggedIn = false;
    });
    return false;
  }

  static async getResourceS3prefix(
    res_id: string,
  ): Promise<{ bucket: string; prefix: string } | null> {
    try {
      const response = await fetch(`/hsapi/resource/s3/${res_id}/`, {
        credentials: "include",
      });

      if (response.ok) {
        const data = await response.json();
        return { bucket: data.bucket, prefix: data.prefix };
      }
    } catch (e: any) {
      const message = `Failed to get S3 prefix for resource ${res_id}: ${e.message}`;
      Notifications.toast({ message, type: "error" });
      throw new Error(message);
    }
    return null;
  }

  static async getCSRFToken(forceRefresh = false): Promise<string | null> {
    if (!forceRefresh && this.$state.CSRFToken) {
      return this.$state.CSRFToken;
    }

    try {
      await fetch(`/csrf-cookie/`, { credentials: "include" });
      const token = this._readCSRFCookie();
      if (token) {
        await User.commit((state) => {
          state.CSRFToken = token;
        });
        return token;
      }
    } catch (e) {
      // ignore
    }

    const token = this._readCSRFCookie();
    if (token) {
      await User.commit((state) => {
        state.CSRFToken = token;
      });
      return token;
    }

    await User.commit((state) => {
      state.CSRFToken = "";
    });
    return User.$state.CSRFToken;
  }

  private static _readCSRFCookie(): string | null {
    for (const cookie of document.cookie.split(";")) {
      const [name, value] = cookie.trim().split("=");
      if (name === "csrftoken") return decodeURIComponent(value);
    }
    return null;
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
