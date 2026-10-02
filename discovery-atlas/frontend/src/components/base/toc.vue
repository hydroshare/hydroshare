<template>
  <!-- The <aside> stays in normal flow purely to reserve the column; the
       inner block is what gets pinned. -->
  <aside v-if="isTocReady && toc.length" id="app-toc" ref="tocEl">
    <div
      class="toc-inner"
      :class="{ 'is-pinned': pinned }"
      :style="pinnedStyle"
    >
      <div class="toc-title">On this page</div>

      <ul>
        <li
          v-for="item of toc"
          :key="item.to"
          :class="[
            'toc-item',
            {
              active: activeItem === item.to,
              'toc-nested': item.level && item.level >= 4,
            },
          ]"
        >
          <a
            href="#"
            class="toc-link"
            @click.prevent="onClick(item.to)"
            v-text="item.text"
          />
        </li>
      </ul>
    </div>
  </aside>
</template>

<script setup lang="ts">
import User from "@/models/user.model";
import { pickActiveSection, type TocOffset } from "@/components/base/toc-active";

const activeItem = ref("");
const tocEl = ref<HTMLElement | null>(null);
const pinned = ref(false);

const toc = computed(() => User.$state.toc);
const isTocReady = computed(() => User.$state.isTocReady);

const box = ref({ top: 0, left: 0, width: 0, maxHeight: 0 });

// `position: fixed`, not `transform`. A transform contributes to the
// document's scrollable overflow, so translating the TOC grew the body, the
// host's ResizeObserver grew the iframe, the clamp changed, and the whole
// thing oscillated. Fixed elements are out of flow and contribute nothing to
// overflow, so the loop cannot form.
//
// Inside this iframe `position: fixed` resolves against the iframe viewport,
// which spans the entire document and never scrolls — so `top` behaves like
// an absolute document offset and we drive it from the parent's scroll.
const pinnedStyle = computed(() =>
  pinned.value
    ? {
        position: "fixed" as const,
        top: `${box.value.top}px`,
        left: `${box.value.left}px`,
        width: `${box.value.width}px`,
        maxHeight: `${box.value.maxHeight}px`,
        overflowY: "auto" as const,
      }
    : undefined,
);

/**
 * Height of fixed chrome pinned to the top of the parent window (HydroShare
 * renders a `navbar-fixed-top`), so the TOC doesn't slide underneath it.
 *
 * Cached: this walks the parent's entire DOM, which is far too expensive to
 * repeat on every scroll frame — doing so was itself the source of the lag.
 * Chrome height only changes on resize, so recompute there.
 */
let cachedInset: number | null = null;

function parentTopInset(parentWin: Window): number {
  if (cachedInset !== null) return cachedInset;
  let inset = 0;
  try {
    const vw = parentWin.innerWidth;
    parentWin.document.body.querySelectorAll("*").forEach((el) => {
      const s = parentWin.getComputedStyle(el);
      if (s.position !== "fixed" && s.position !== "sticky") return;
      if (s.visibility === "hidden" || s.display === "none") return;
      const r = el.getBoundingClientRect();
      if (r.width < vw * 0.5 || r.height <= 0 || r.height > 200) return;
      if (r.top <= 1 && r.bottom > inset) inset = r.bottom;
    });
  } catch {
    /* cross-origin */
  }
  cachedInset = inset;
  return inset;
}

// `position: sticky` cannot work here: the iframe has scrolling="no" and is
// auto-sized to its content, so it never scrolls and there is no scrolling
// ancestor for sticky to resolve against — the PARENT window scrolls.
function updatePinned() {
  const aside = tocEl.value;
  if (!aside) return;

  const frame = window.frameElement as HTMLIFrameElement | null;
  const parentWin = window.parent;
  if (!frame || !parentWin || parentWin === window) {
    // Standalone (not embedded): native `position: sticky` in CSS handles it.
    pinned.value = false;
    return;
  }

  try {
    const parentScrollY = parentWin.scrollY || parentWin.pageYOffset || 0;
    const iframeTop = frame.getBoundingClientRect().top + parentScrollY;
    const inset = parentTopInset(parentWin);

    // The <aside> is still in flow, so its rect gives us the column geometry
    // to match. Read it while unpinned-or-pinned — width/left don't change.
    const rect = aside.getBoundingClientRect();

    box.value = {
      top: Math.round(parentScrollY + inset + 16 - iframeTop),
      left: Math.round(rect.left),
      width: Math.round(aside.clientWidth),
      maxHeight: Math.max(160, parentWin.innerHeight - inset - 32),
    };
    pinned.value = true;
  } catch {
    pinned.value = false;
  }

  updateActive();
}

// Scroll-spy. `activeItem` previously only ever changed on click, so the
// highlight was wrong the moment a user scrolled by hand.
function updateActive() {
  const parentWin = window.parent;
  let bandTop = 0;
  try {
    const frame = window.frameElement as HTMLIFrameElement | null;
    if (frame && parentWin && parentWin !== window) {
      const parentScrollY = parentWin.scrollY || 0;
      const iframeTop = frame.getBoundingClientRect().top + parentScrollY;
      bandTop = parentScrollY + parentTopInset(parentWin) - iframeTop;
    } else {
      bandTop = window.scrollY;
    }
  } catch {
    bandTop = window.scrollY;
  }

  const offsets: TocOffset[] = [];
  for (const item of toc.value) {
    const el = document.querySelector(item.to) as HTMLElement | null;
    if (!el) continue;
    offsets.push({ to: item.to, offsetTop: el.offsetTop });
  }

  // +80px so a heading counts as "current" slightly before it hits the top.
  const current = pickActiveSection(offsets, bandTop + 80);
  if (current) activeItem.value = current;
}

// Scroll of the parent's document is observed with a CAPTURE-phase listener.
// A bubble-phase listener registered on the parent window from inside this
// iframe was not firing for the parent's document scroll, so the TOC computed
// its position once at mount and then sat still.
//
// rAF polling is deliberately not used as the driver: the browser throttles
// animation frames hard for a tall iframe that is mostly outside the parent's
// viewport (measured ~3fps here), which is exactly our situation.
function onScroll() {
  updatePinned();
}

function onResize() {
  cachedInset = null; // chrome height can change with the viewport
  updatePinned();
}

// Backstop poll. Cross-frame scroll events proved intermittent here, and rAF
// is throttled for a mostly-offscreen iframe, so neither alone keeps the TOC
// in sync. A 60ms timer is immune to both; the body early-outs on an
// unchanged scroll position, so the steady-state cost is two property reads.
let poll = 0;
let lastY = -1;

function pollTick() {
  try {
    const y = window.parent.scrollY || window.parent.pageYOffset || 0;
    if (y === lastY) return;
    lastY = y;
  } catch {
    /* cross-origin */
  }
  updatePinned();
}

function bindParent(bind: boolean) {
  const fn = bind ? "addEventListener" : "removeEventListener";
  try {
    const parentWin = window.parent;
    if (parentWin && parentWin !== window) {
      parentWin[fn]("scroll", onScroll, true);
      parentWin[fn]("resize", onResize, true);
    }
  } catch {
    /* cross-origin */
  }
  window[fn]("scroll", onScroll, true);
  window[fn]("resize", onResize, true);

  if (bind) {
    if (!poll) poll = window.setInterval(pollTick, 60);
  } else if (poll) {
    clearInterval(poll);
    poll = 0;
  }
}

onMounted(() => {
  bindParent(true);
  nextTick(updatePinned);
});
onBeforeUnmount(() => bindParent(false));

function onClick(hash: string): void {
  const el = document.querySelector(hash) as HTMLElement | null;
  if (!el) return;
  activeItem.value = hash;

    // The iframe has scrolling="no" and is sized to fit content, so
    // `window.scrollTo` inside the iframe is a no-op — the parent owns the
    // scroll. Reach across to the parent window (same-origin) and scroll
    // there.
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
          // Cross-origin — fall through to in-iframe scroll.
        }
      }
    }

    const top = el.getBoundingClientRect().top + window.scrollY - 16;
    window.scrollTo({ top, behavior: "smooth" });
  }
</script>

<style lang="scss" scoped>
#app-toc {
  // Stays in flow to reserve the column; .toc-inner is what gets pinned.
  align-self: stretch;
  width: 220px;
  flex-shrink: 0;
  padding: 0.25rem 0 0.5rem;
}

.toc-inner {
  // Standalone (not embedded in the host iframe) native sticky is enough.
  // Embedded, `is-pinned` swaps in `position: fixed` with a computed top —
  // see updatePinned() for why sticky and transform both fail there.
  position: sticky;
  top: 1rem;

  // No transition: `top` IS the scroll position, so easing it makes the TOC
  // visibly trail the page rather than track it.
  &.is-pinned {
    // inline styles supply position/top/left/width/max-height
    scrollbar-width: thin;
  }
}

.toc-title {
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.45);
  padding: 0 0 0.5rem 0.875rem;
}

// Below 1440px (typical 13"/14" laptops at native scale), the 220px TOC plus
// the shell gap is too greedy. Shrink the sidebar and the inner spacing.
@media (max-width: 1439px) {
  #app-toc {
    width: 170px;
    font-size: 0.875rem;
  }
}

// Below 1100px, hide the TOC altogether — the content is too narrow for a
// usable sidebar at that point. Users on small screens can still navigate via
// browser-native page scroll.
@media (max-width: 1099px) {
  #app-toc {
    display: none;
  }
}

#app-toc ul {
  list-style-type: none;
  padding-left: 0;
  margin: 0;
  // A continuous rail behind the items, so the active marker reads as a
  // position along the page rather than a detached coloured tick.
  border-left: 1px solid rgba(0, 0, 0, 0.09);
}

.toc-item {
  position: relative;
  font-size: 0.8125rem;
  line-height: 1.25rem;
  color: rgba(0, 0, 0, 0.6);
  transition: color 0.15s ease, background-color 0.15s ease;
  border-radius: 0 4px 4px 0;

  // The active rail segment sits on top of the shared 1px track.
  &::before {
    content: "";
    position: absolute;
    left: -1px;
    top: 0;
    bottom: 0;
    width: 2px;
    background-color: transparent;
    transition: background-color 0.15s ease;
  }

  &:hover {
    color: rgba(0, 0, 0, 0.87);
    background-color: rgba(0, 0, 0, 0.035);
  }

  &.active {
    color: #4bb5c1;
    font-weight: 600;

    &::before {
      background-color: #4bb5c1;
    }
  }

  &.toc-nested {
    font-size: 0.75rem;

    .toc-link {
      padding-left: 1.75rem;
    }
  }
}

.toc-link {
  display: block;
  color: inherit;
  text-decoration: none;
  padding: 0.3125rem 0.5rem 0.3125rem 0.875rem;

  &:focus-visible {
    outline: 2px solid #4bb5c1;
    outline-offset: -2px;
    border-radius: 4px;
  }
}
</style>
