/**
 * What every URL-building result shares (ADR-0011 §2): the `[MAP_KEY]` placeholder and where a
 * key comes from (FR-URL-002), the fixed limitations statement (FR-URL-003), and the FIRMS pages
 * offered alongside (FR-URL-004).
 */
import { MISSING_DATA_PAGE } from "../knowledge/missing-data.js";

export const FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov";
export const MAP_KEY_PLACEHOLDER = "[MAP_KEY]";
export const MAP_KEY_SIGNUP_URL = `${FIRMS_BASE_URL}/api/map_key/`;
export const ARCHIVE_DOWNLOAD_URL = `${FIRMS_BASE_URL}/download/`;

/** The FAQ entry that explains why standard data are preferred; cited, never paraphrased. */
export const SP_VS_NRT_ENTRY =
  "faq.getting-started.what-are-the-key-differences-between-urt-rt-nrt-and-standard";

export const LIMITATIONS =
  "This server builds URLs only. It has not opened them, and it cannot fetch, summarize, count, or chart the data they return. Open a URL (with a MAP_KEY in place of [MAP_KEY] where there is one) to see the data.";

export interface MapKeyGuidance {
  placeholder: typeof MAP_KEY_PLACEHOLDER;
  get_a_key: string;
  where_it_goes: string;
}

export const MAP_KEY_GUIDANCE: MapKeyGuidance = {
  placeholder: MAP_KEY_PLACEHOLDER,
  get_a_key: MAP_KEY_SIGNUP_URL,
  where_it_goes:
    "Replace [MAP_KEY] in the URL with your FIRMS MAP_KEY (32 letters and digits). FIRMS emails a key for free from the sign-up page.",
};

export interface RelatedLinks {
  data_availability_url: string;
  missing_data_page: string;
  archive_download_page: string;
  map_key_page: string;
}

/** FIRMS API `data_availability`: the publicly advertised way to check date coverage. */
export function dataAvailabilityUrl(sensor = "ALL"): string {
  return `${FIRMS_BASE_URL}/api/data_availability/csv/${MAP_KEY_PLACEHOLDER}/${sensor}`;
}

/** Transactions a MAP_KEY has used in the current interval. */
export function mapKeyStatusUrl(): string {
  return `${FIRMS_BASE_URL}/mapserver/mapkey_status/?MAP_KEY=${MAP_KEY_PLACEHOLDER}`;
}

export function relatedLinks(): RelatedLinks {
  return {
    data_availability_url: dataAvailabilityUrl(),
    missing_data_page: MISSING_DATA_PAGE,
    archive_download_page: ARCHIVE_DOWNLOAD_URL,
    map_key_page: MAP_KEY_SIGNUP_URL,
  };
}
