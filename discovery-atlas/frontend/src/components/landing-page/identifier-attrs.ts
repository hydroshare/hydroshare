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

/**
 * Converts the schema.org `identifier` array format used by Creator/
 * Contributor (`[{ "@type": "PropertyValue", propertyID, value }, ...]`) into
 * the `{ propertyID: value }` dict shape `listIdentifiers` expects.
 * `HydroShareID` is excluded — that entry backs the "Profile" button
 * (`profileLink`), not the icon row, so including it here would render it
 * twice.
 */
export function personIdentifiersToRecord(
  identifiers: Array<{ propertyID?: string; value?: string }> | null | undefined,
): Record<string, string> {
  if (!Array.isArray(identifiers)) return {};
  const record: Record<string, string> = {};
  for (const item of identifiers) {
    if (
      item &&
      typeof item.propertyID === "string" &&
      item.propertyID !== "HydroShareID" &&
      typeof item.value === "string" &&
      item.value.trim().length > 0
    ) {
      record[item.propertyID] = item.value;
    }
  }
  return record;
}
