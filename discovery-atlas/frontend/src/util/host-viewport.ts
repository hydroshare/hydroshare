/**
 * Dialog placement for the HydroShare host page.
 *
 * HydroShare embeds this app in a same-origin iframe with `scrolling="no"`,
 * sized to its content by a ResizeObserver. The iframe viewport is therefore
 * the entire document, so a dialog centred against it lands at the midpoint of
 * the whole page rather than of what the user is looking at. HydroShare also
 * renders a `navbar-fixed-top` over the top of the parent viewport, so the
 * usable band is inset by it.
 *
 * Published as CSS custom properties on <html> and consumed by the rules in
 * assets/css/host-dialogs.scss, which target the dialog classes cznet-vue-core
 * puts on its overlay content. The library itself knows none of this.
 */

export interface HostViewportBand {
  top: number;
  maxHeight: number;
}

/** Height of fixed/sticky bars pinned to the top and bottom of a window. */
function chromeInsets(win: Window): { top: number; bottom: number } {
  let top = 0;
  let bottom = 0;
  try {
    const vw = win.innerWidth;
    const vh = win.innerHeight;
    win.document.body?.querySelectorAll("*").forEach((el: Element) => {
      const s = win.getComputedStyle(el);
      if (s.position !== "fixed" && s.position !== "sticky") return;
      if (s.visibility === "hidden" || s.display === "none") return;
      const r = el.getBoundingClientRect();
      if (r.width < vw * 0.5 || r.height <= 0 || r.height > vh * 0.4) return;
      if (r.top <= 1 && r.bottom > top) top = r.bottom;
      if (r.bottom >= vh - 1 && vh - r.top > bottom) bottom = vh - r.top;
    });
  } catch {
    // cross-origin
  }
  return { top, bottom };
}

/**
 * The band of the iframe the parent window is showing, clear of fixed chrome.
 * Null when standalone or cross-origin, which leaves Vuetify's own centring.
 */
export function getHostViewportBand(gutter = 24): HostViewportBand | null {
  try {
    const frame = window.frameElement as HTMLIFrameElement | null;
    const parentWin = window.parent;
    if (!frame || !parentWin || parentWin === window) return null;

    const parentScrollY = parentWin.scrollY || parentWin.pageYOffset || 0;
    const iframeTop = frame.getBoundingClientRect().top + parentScrollY;
    const chrome = chromeInsets(parentWin);

    const usable = Math.max(
      240,
      parentWin.innerHeight - chrome.top - chrome.bottom,
    );
    const visibleTop = Math.max(0, parentScrollY + chrome.top - iframeTop);

    return {
      top: visibleTop + gutter,
      maxHeight: Math.max(240, usable - gutter * 2),
    };
  } catch {
    return null;
  }
}

/**
 * Publish the band as CSS vars on <html> and keep them current. `hs-embedded`
 * gates the stylesheet so nothing applies when not embedded.
 */
export function trackHostViewport(): void {
  const root = document.documentElement;

  const publish = () => {
    const band = getHostViewportBand();
    if (!band) {
      root.classList.remove("hs-embedded");
      return;
    }
    root.classList.add("hs-embedded");
    root.style.setProperty("--hs-dialog-top", `${band.top}px`);
    root.style.setProperty("--hs-dialog-max-h", `${band.maxHeight}px`);
  };

  publish();

  try {
    const parentWin = window.parent;
    if (parentWin && parentWin !== window) {
      parentWin.addEventListener("scroll", publish, { passive: true });
      parentWin.addEventListener("resize", publish);
    }
  } catch {
    // cross-origin
  }
}
