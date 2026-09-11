// Shared metadata for the external profile identifiers shown in author/owner
// profile dropdowns. Mirrors the `identifierAttributes` map in the legacy
// theme/static/js/hs-vue/left-header-app.js so labels and icons stay in sync.
//
// Icon files are served by Django from theme/static/img/ — the iframe is
// same-origin, so absolute /static/static/... URLs resolve correctly.

export interface IdentifierAttrs {
  title: string;
  src: string;
}

export const identifierAttributes: { [key: string]: IdentifierAttrs } = {
  ORCID: {
    title: "ORCID",
    src: "/static/static/img/orcid.logo.icon.svg",
  },
  ResearchGateID: {
    title: "ResearchGate",
    src: "/static/static/img/researchgate.png",
  },
  ResearcherID: {
    title: "ResearcherID",
    src: "/static/static/img/researcherID.png",
  },
  GoogleScholarID: {
    title: "Google Scholar",
    src: "/static/static/img/google-scholar.svg",
  },
};

export interface IdentifierItem {
  key: string;
  url: string;
  attrs?: IdentifierAttrs;
}

/** Normalize an identifiers dict ({ ORCID: "url", ... }) into a render-ready list. */
export function listIdentifiers(
  identifiers: Record<string, string> | null | undefined,
): IdentifierItem[] {
  if (!identifiers || typeof identifiers !== "object") return [];
  return Object.entries(identifiers)
    .filter(([, url]) => typeof url === "string" && url.trim().length > 0)
    .map(([key, url]) => ({
      key,
      url,
      attrs: identifierAttributes[key],
    }));
}
