<template>
  <aside
    v-if="isTocReady && toc.length"
    id="app-toc"
  >
    <div class="toc-title text-caption font-weight-bold text-uppercase text-medium-emphasis mt-4 mb-2 ms-4">
      On this page
    </div>

    <ul class="ms-4 me-2">
      <li
        v-for="item of toc"
        :key="item.to"
        :class="[
          'toc-item text-body-2 py-1',
          {
            'active': activeItem === item.to,
            'toc-nested': item.level && item.level >= 4,
          },
        ]"
      >
        <a
          href="#"
          class="toc-link d-block text-decoration-none"
          @click.prevent="onClick(item.to)"
          v-text="item.text"
        />
      </li>
    </ul>
  </aside>
</template>

<script lang="ts">
import { Component, Vue, toNative } from "vue-facing-decorator";
import User from "@/models/user.model";

@Component({
  name: "toc",
  components: {},
})
class Toc extends Vue {
  activeItem = "";

  get toc() {
    return User.$state.toc;
  }

  get isTocReady() {
    return User.$state.isTocReady;
  }

  onClick(hash: string): void {
    const el = document.querySelector(hash) as HTMLElement | null;
    if (!el) return;
    this.activeItem = hash;

    // When mounted inside the resource landing iframe (scrolling="no", height
    // auto-fits content), the iframe itself never scrolls — the parent does.
    // Reach out to the parent window directly (same-origin) and scroll it to
    // the element's absolute position.
    if (window.parent && window.parent !== window) {
      const frame = window.frameElement as HTMLIFrameElement | null;
      if (frame) {
        try {
          const parentWin = window.parent as Window;
          const iframeTop =
            frame.getBoundingClientRect().top +
            (parentWin.scrollY || parentWin.pageYOffset || 0);
          const elTop = el.getBoundingClientRect().top;
          parentWin.scrollTo({ top: iframeTop + elTop - 16, behavior: "smooth" });
          return;
        } catch {
          // Cross-origin or other failure — fall back to in-iframe scroll.
        }
      }
    }

    const top = el.getBoundingClientRect().top + window.scrollY - 16;
    window.scrollTo({ top, behavior: "smooth" });
  }
}

export default toNative(Toc);
</script>

<style lang="scss" scoped>
#app-toc {
  position: sticky;
  top: 1rem;
  align-self: flex-start;
  width: 220px;
  flex-shrink: 0;
  padding-top: 0.5rem;
  max-height: calc(100vh - 2rem);
  overflow-y: auto;
}

#app-toc ul {
  list-style-type: none;
  padding-left: 0;
}

.toc-item {
  padding-left: 12px;
  border-left: 2px solid transparent;
  transition: border-color 0.15s, color 0.15s;
  color: rgba(0, 0, 0, 0.54);

  &:hover {
    color: rgba(0, 0, 0, 0.87);
  }

  &.active {
    border-left-color: rgb(var(--v-theme-primary));
    color: rgb(var(--v-theme-primary));
    font-weight: 500;
  }

  &.toc-nested {
    padding-left: 24px;
    font-size: 0.8125rem;
  }
}

.toc-link {
  color: inherit;
}
</style>
