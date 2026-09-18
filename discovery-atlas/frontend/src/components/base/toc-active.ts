export interface TocOffset {
  to: string;
  offsetTop: number;
}

// The section sitting lowest on the page while still at or above the band.
export function pickActiveSection(offsets: TocOffset[], band: number): string {
  let active = "";
  let best = -Infinity;

  for (const { to, offsetTop } of offsets) {
    if (offsetTop <= band && offsetTop > best) {
      best = offsetTop;
      active = to;
    }
  }

  return active;
}
