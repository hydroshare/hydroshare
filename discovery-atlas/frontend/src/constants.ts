export const APP_NAME = import.meta.env.VITE_APP_NAME;
export const APP_BASE = import.meta.env.VITE_APP_BASE;
export const APP_URL = import.meta.env.VITE_APP_URL;
export const API_BASE = import.meta.env.VITE_APP_API_URL;
export const APP_ORIGIN = import.meta.env.VITE_APP_ORIGIN
export const DEFAULT_TOAST_DURATION = 3500;
export const COMPANION_URL = import.meta.env.VITE_APP_COMPANION_URL || "http://localhost/companion";
export const GOOGLE_PICKER_CLIENT_ID = import.meta.env.VITE_APP_GOOGLE_PICKER_CLIENT_ID || "";
export const GOOGLE_PICKER_API_KEY = import.meta.env.VITE_APP_GOOGLE_PICKER_API_KEY || "";
export const GOOGLE_PICKER_APP_ID = import.meta.env.VITE_APP_GOOGLE_PICKER_APP_ID || "";

// Origin of the hs-s3-proxy service, which authenticates S3 requests with
// the Django session/CSRF cookies instead of minio access keys. Locally the
// proxy is published on host port 9002; deployed environments serve it on
// the s3. subdomain of the app host.
export const S3_PROXY_URL: string =
  import.meta.env.VITE_APP_S3_PROXY_URL ||
  (["localhost", "127.0.0.1"].includes(window.location.hostname)
    ? `${window.location.protocol}//${window.location.hostname}:9002`
    : `${window.location.protocol}//s3.${window.location.hostname}`);


export const sameRouteNavigationErrorHandler = (e) => {
  // Ignore the vuex err regarding  navigating to the page they are already on.
  if (
    e.name !== "NavigationDuplicated" &&
    !e.message.includes("Avoided redundant navigation to current location")
  ) {
    // But print any other errors to the console
    console.error(e);
  }
};

export const MAX_YEAR = new Date().getFullYear();
export const MIN_YEAR = 2010;
export const ENDPOINTS: { [key: string]: string } = {
  search: `${API_BASE}/search`,
  typeahead: `${API_BASE}/typeahead`,
  typeaheadCreator: `${API_BASE}/typeahead_creator`,
  contentTypes: `${API_BASE}/content-types`,
};
export const INITIAL_RANGE: [number, number] = [MIN_YEAR, MAX_YEAR];

export const contentTypeLogos: { [key: string]: string } = {
  CompositeResource: new URL("/img/composite48x48.png", import.meta.url).href,
  CollectionResource: new URL("/img/collection48x48.png", import.meta.url).href,
  GeographicRasterAggregation: new URL(
    "/img/geographicraster48x48.png",
    import.meta.url,
  ).href,
  TimeSeriesAggregation: new URL("/img/timeseries48x48.png", import.meta.url)
    .href,
  GeographicFeatureAggregation: new URL(
    "/img/geographicfeature48x48.png",
    import.meta.url,
  ).href,
  MultidimensionalAggregation: new URL(
    "/img/multidimensional48x48.png",
    import.meta.url,
  ).href,
};

export const sharingStatusIcons: { [key: string]: string } = {
  PUBLIC: new URL("/img/public.png", import.meta.url).href,
  PRIVATE: new URL("/img/private.png", import.meta.url).href,
  DISCOVERABLE: new URL("/img/discoverable.png", import.meta.url).href,
  PUBLISHED: new URL("/img/published.png", import.meta.url).href,
  SPATIAL: new URL("/img/Globe-Green.png", import.meta.url).href,
};

export const sharingStatusOptions = [
  {
    value: "Discoverable",
    label: "Discoverable",
    hint: "Metadata is public but data are protected.",
    icon: sharingStatusIcons.DISCOVERABLE,
  },
  {
    value: "Public",
    label: "Public",
    hint: "Can be viewed and downloaded by anyone.",
    icon: sharingStatusIcons.PUBLIC,
  },
  {
    value: "Published",
    label: "Published",
    hint: "Has a digital object identifier (DOI) and content files which cannot be changed.",
    icon: sharingStatusIcons.PUBLISHED,
  },
]

export const contentTypeLabels: { [key: string]: string } = {
  CompositeResource: "Composite Resource",
  CollectionResource: "Collection",
  TimeSeriesAggregation: "Time Series",
  "CSV Data": "CSV Data",
  Document: "Document",
  "File Set": "File Set",
  "Generic Data": "Generic Data",
  GeographicFeatureAggregation: "Geographic Feature (ESRI Shapefiles)",
  GeographicRasterAggregation: "Geographic Raster",
  MultidimensionalAggregation: "Multidimensional (NetCDF)",
  Image: "Image",
};