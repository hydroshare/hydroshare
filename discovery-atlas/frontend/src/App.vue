<template>
  <v-app app>
    <v-app-bar
      v-if="!$route.meta.hideNavigation"
      ref="appBar"
      id="app-bar"
      elevate-on-scroll
      fixed
      app
    >
      <v-container class="d-flex align-end full-height pa-0 align-center">
        <router-link :to="{ path: `/` }" class="logo">
          <img src="/img/hydroshare.png" alt="HydroShare" />
        </router-link>
        <div class="spacer"></div>
        <div v-if="!$vuetify.display.mdAndDown" class="d-flex gap-1 ml-6">
          <v-btn
            color="black"
            v-for="path of paths"
            :key="path.attrs.to || path.attrs.href"
            v-bind="path.attrs"
            :id="`navbar-nav-${path.label.replaceAll(/[\/\s]/g, ``)}`"
            :elevation="0"
            active-class="primary"
            :class="path.isActive?.() ? 'primary' : ''"
          >
            {{ path.label }}
          </v-btn>
        </div>

        <v-spacer></v-spacer>

        <template v-if="!$vuetify.display.mdAndDown">
          <v-btn
            v-if="!isLoggedIn"
            id="navbar-login"
            variant="elevated"
            rounded
            @click="openLogInDialog()"
          >
            Log In
          </v-btn>
          <template v-else>
            <v-menu bottom left>
              <template #activator="{ props }">
                <v-btn
                  :color="
                    route.matched.some(
                      (p: RouteLocationMatched) => p.name === 'profile',
                    )
                      ? 'primary'
                      : 'white'
                  "
                  v-bind="props"
                  variant="elevated"
                  rounded
                >
                  <v-icon>mdi-account-circle</v-icon>
                  <v-icon>mdi-menu-down</v-icon>
                </v-btn>
              </template>

              <v-list class="pa-0">
                <v-list-item
                  :to="{ path: '/profile' }"
                  active-class="bg-primary"
                  prepend-icon="mdi-account-circle"
                >
                  <v-list-item-title> Account & Settings </v-list-item-title>
                </v-list-item>

                <v-divider />

                <v-list-item
                  id="navbar-logout"
                  prepend-icon="mdi-logout"
                  @click="logOut()"
                >
                  <v-list-item-title>Log Out</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </template>
        </template>

        <v-app-bar-nav-icon
          v-if="$vuetify.display.mdAndDown"
          @click.stop="showMobileNavigation = true"
        />
      </v-container>
    </v-app-bar>

    <v-main app>
      <v-container id="main-container">
        <v-sheet min-height="70vh">
          <router-view name="content" :key="$route.fullPath" />
        </v-sheet>
      </v-container>
    </v-main>

    <v-footer class="mt-8 bg-grey-lighten-4">
      <router-view name="footer" />
    </v-footer>

    <!-- NOTE: v-navigation-drawer is a single component for the entire app. Properties of other v-navigation-drawer instances will affect this one. -->

    <v-navigation-drawer
      v-model="showMobileNavigation"
      class="mobile-nav-items"
      temporary
      app
    >
      <v-list nav density="compact" class="nav-items">
        <v-list-item class="text-body-1">
          <v-list-item
            v-for="path of paths"
            :id="`drawer-nav-${path.label.replaceAll(/[\/\s]/g, ``)}`"
            :key="path.attrs.to || path.attrs.href"
            v-bind="path.attrs"
            active-class="bg-primary"
            :class="path.isActive && path.isActive() ? 'primary' : ''"
            @click="showMobileNavigation = false"
          >
            <v-icon class="mr-2">
              {{ path.icon }}
            </v-icon>
            <span>{{ path.label }}</span>
            <v-icon v-if="path.isExternal" small class="ml-2" right>
              mdi-open-in-new
            </v-icon>
          </v-list-item>
        </v-list-item>

        <v-divider class="my-4" />

        <v-list-item class="text-body-1">
          <v-list-item
            v-if="!isLoggedIn"
            id="drawer-nav-login"
            @click="
              openLogInDialog();
              showMobileNavigation = false;
            "
          >
            <v-icon class="mr-2"> mdi-login </v-icon>
            <span>Log In</span>
          </v-list-item>

          <template v-else>
            <v-list-item
              :to="{ path: '/profile' }"
              prepend-icon="mdi-account-circle"
            >
              <span>Account & Settings</span>
            </v-list-item>

            <v-list-item
              id="drawer-nav-logout"
              prepend-icon="mdi-logout"
              @click="logOut()"
            >
              <span>Log Out</span>
            </v-list-item>
          </template>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <cz-notifications />

    <v-dialog v-model="logInDialog.isActive" width="500">
      <cz-login
        @cancel="logInDialog.isActive = false"
        @logged-in="logInDialog.onLoggedIn"
      />
    </v-dialog>

    <link
      href="https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900"
      rel="stylesheet"
    />
    <link
      href="https://cdn.jsdelivr.net/npm/@mdi/font@6.x/css/materialdesignicons.min.css"
      rel="stylesheet"
    />
  </v-app>
</template>

<script lang="ts">
import { Component, Vue, toNative } from "vue-facing-decorator";
import { APP_NAME } from "./constants";
import { CzNotifications, Notifications } from "@cznethub/cznet-vue-core";
import { Subscription } from "rxjs";
import User from "@/models/user.model";
import CzLogin from "@/components/account/cz.login.vue";
import { addRouteTags } from "./modules/router";
import { useRoute, RouteLocationRaw } from "vue-router";
import { useRouter } from "vue-router";
import Search from "./models/search.model";

@Component({
  name: "app",
  components: { CzNotifications, CzLogin },
})
class App extends Vue {
  route = useRoute();
  router = useRouter();
  protected onOpenLogInDialog!: Subscription;
  public showMobileNavigation = false;
  protected logInDialog: any & { isActive: boolean } = {
    isActive: false,
    onLoggedIn: () => {},
    onCancel: () => {},
  };

  protected getOriginUrl() {
    return window.location.origin;
  }

  public paths: any[] = [
    {
      attrs: { href: `${this.getOriginUrl()}/home/` },
      label: "Home",
      icon: "mdi-home",
    },
    {
      attrs: { href: `${this.getOriginUrl()}/my-resources/` },
      label: "My Resources",
      icon: "mdi-home",
    },
    {
      attrs: { to: "/" },
      label: "Discover",
      icon: "mdi-home",
    },
    {
      attrs: { href: `${this.getOriginUrl()}/apps/` },
      label: "Apps",
      icon: "mdi-home",
    },
    {
      attrs: { href: "https://help.hydroshare.org/" },
      label: "Help",
      icon: "mdi-home",
      isExternal: true,
    },
  ];

  protected get isLoggedIn(): boolean {
    return User.$state.isLoggedIn;
  }

  protected logOut() {
    Notifications.openDialog({
      title: "Log out?",
      content: "Are you sure you want to log out?",
      confirmText: "Log Out",
      cancelText: "Cancel",
      onConfirm: () => {
        User.logOut();
      },
    });
  }

  async created() {
    document.title = APP_NAME;
    addRouteTags(this.route, this.route);

    // User.fetchSchemas();

    this.onOpenLogInDialog = User.logInDialog$.subscribe(
      (redirectTo?: RouteLocationRaw) => {
        this.logInDialog.isActive = true;

        this.logInDialog.onLoggedIn = () => {
          if (redirectTo) this.router.push(redirectTo).catch(() => {});

          this.logInDialog.isActive = false;
        };
      },
    );

    try {
      Search.fetchContentTypes();
    } catch (e) {
      console.error("Failed to fetch content types", e);
    }
  }

  beforeDestroy() {
    // Good practice
    this.onOpenLogInDialog.unsubscribe();
  }

  protected openLogInDialog() {
    User.openLogInDialog();
  }
}
export default toNative(App);
</script>

<style lang="scss" scoped>
.logo {
  height: 36px;
  cursor: pointer;

  img {
    height: 100%;
  }
}

#footer {
  width: 100%;
  margin: 0;
  min-height: unset;
  margin-top: 4rem;
  box-shadow: none;
}

.v-toolbar.v-app-bar--is-scrolled > .v-toolbar__content > .container {
  align-items: center !important;
  will-change: padding;
  padding-top: 0;
  padding-bottom: 0;
}

.nav-items {
  border-radius: 2rem !important;
  overflow: hidden;

  & > a.v-btn:first-child {
    border-top-left-radius: 2rem !important;
    border-bottom-left-radius: 2rem !important;
  }

  & > a.v-btn:last-child {
    border-top-right-radius: 2rem !important;
    border-bottom-right-radius: 2rem !important;
  }

  .v-btn {
    margin: 0;
    border-radius: 0;
    height: 39px !important;
  }
}

// .nav-items .v-btn.is-active,
// .mobile-nav-items .v-list-item.is-active {
//   background-color: #1976d2 !important;
//   color: #FFF;
// }
</style>
